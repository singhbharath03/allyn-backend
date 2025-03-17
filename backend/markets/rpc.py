import logging
import asyncio
from typing import List, Optional

from tools.dictionary import get_from_dict
from markets.constants import SOL_DECIMALS
from tools.http import req_post

RPC_URL = "https://api.testnet.v1.sonic.game"

BATCH_REQUEST_SIZE = 100


async def get_program_accounts(pubkey: str):
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getProgramAccounts",
        "params": [
            pubkey,
            {"encoding": "base64"},
        ],
    }

    return await rpc_request(req)


async def get_transactions(tx_ids: List[str]):
    requests = [
        {
            "jsonrpc": "2.0",
            "id": tx_id,
            "method": "getTransaction",
            "params": [
                tx_id,
                {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0},
            ],
        }
        for tx_id in tx_ids
    ]

    results = await batched_rpc_requests(requests, BATCH_REQUEST_SIZE)

    resps = []
    for result in results:
        if "result" in result:
            resps.append(result["result"])
        else:
            logging.error("Failed to get transaction: %s", result)

    return resps


async def get_user_token_accounts(pubkey):
    resp = await rpc_request(get_accounts_by_owner_request(pubkey))

    return get_token_accounts_and_balances_by_mints(resp)


async def get_token_largest_accounts(token_address: str):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenLargestAccounts",
        "params": [token_address],
    }

    return await rpc_request(payload)


async def get_user_token_account(pubkey, token_address):
    resp = await rpc_request(get_accounts_by_owner_request(pubkey, token_address))

    token_account_by_token_address, balance_by_token_address = (
        get_token_accounts_and_balances_by_mints(resp)
    )

    return token_account_by_token_address.get(
        token_address
    ), balance_by_token_address.get(token_address)


async def get_all_signatures(
    pubkey: str,
    *,
    until: Optional[str] = None,
    only_successful: bool = True,
    max_loops: int = 1,
):
    signatures = []
    before = None
    loop_count = 0
    while True:
        if loop_count > max_loops:
            logging.error(
                "Exceeded max loops of %s for fetching signatures for %s",
                max_loops,
                pubkey,
            )
            return None

        request = get_signatures_for_addresses_rpc(pubkey, before=before, until=until)

        result = await rpc_request(request)
        if "result" in result:

            new_signatures = result["result"]
            if len(new_signatures) == 0:
                break
            else:
                before = new_signatures[-1]["signature"]
                signatures.extend(
                    get_successful_sig_objs(new_signatures)
                    if only_successful
                    else new_signatures
                )

                if before == until:
                    break
        else:
            logging.error("Failed to get signatures for address: %s", result)
            return None

        loop_count += 1

    return [sig_obj["signature"] for sig_obj in signatures]


async def get_signatures(
    addresses: List[str],
    most_recent_tx_by_addr: dict = {},
    only_successful: bool = True,
) -> dict:
    # Get recent transactions for the address
    requests = [
        get_signatures_for_addresses_rpc(
            address, until=most_recent_tx_by_addr.get(address)
        )
        for address in addresses
    ]
    try:
        results = await batched_rpc_requests(requests, BATCH_REQUEST_SIZE)

        signatures_by_addr = {}
        for result in results:
            if "result" in result:
                address = result["id"]
                signatures = result["result"]
                signatures_by_addr[address] = (
                    get_successful_sig_objs(signatures)
                    if only_successful
                    else signatures
                )
            else:
                logging.error("Failed to get signatures for address: %s", result)
        return signatures_by_addr
    except Exception as e:
        logging.error(f"Error in get_signatures: {str(e)}")
        return {}


def get_signatures_for_addresses_rpc(
    pubkey: str, *, before: Optional[str] = None, until: Optional[str] = None
):
    return {
        "jsonrpc": "2.0",
        "id": pubkey,
        "method": "getSignaturesForAddress",
        "params": [
            pubkey,
            {
                "before": before,
                "until": until,
            },
        ],
    }


async def get_account_infos(pubkeys: List[str]):
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getMultipleAccounts",
        "params": [
            pubkeys,
            {"encoding": "jsonParsed"},
        ],
    }

    results = await rpc_request(data)

    return results


async def get_sol_balance(pubkey: str):
    data = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [pubkey],
    }

    resp = await rpc_request(data)
    if "result" in resp:
        return resp["result"]["value"] / (10**SOL_DECIMALS)

    return None


async def rpc_request(request_body):
    headers = {"Content-Type": "application/json"}

    return await req_post(RPC_URL, request_body, headers=headers)


def get_accounts_by_owner_request(pubkey: str, token_address: Optional[str] = None):
    params = [
        pubkey,
        {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
    ]
    if token_address:
        params[1] = {"mint": token_address}

    params.append({"encoding": "jsonParsed"})

    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": params,
    }


def get_successful_sig_objs(sig_objs: List[dict]):
    return [sig_obj for sig_obj in sig_objs if sig_obj["err"] is None]


def get_token_accounts_and_balances_by_mints(
    token_accounts_by_owner_resp: dict,
):
    get_account_info_values = get_from_dict(
        token_accounts_by_owner_resp, ["result", "value"]
    )
    if get_account_info_values is None:
        logging.error(
            "Failed to get token accounts and balances by mints: %s",
            token_accounts_by_owner_resp,
        )

        return {}, {}

    token_account_by_token_address = {}
    balance_by_token_address = {}
    for account in get_account_info_values:
        parsed_info = account["account"]["data"]["parsed"]["info"]
        mint = parsed_info["mint"]

        parsed_token_details = parsed_info["tokenAmount"]
        amount = float(parsed_token_details["amount"]) / (
            10 ** parsed_token_details["decimals"]
        )

        token_account_by_token_address[mint] = account["pubkey"]
        balance_by_token_address[mint] = amount

    return token_account_by_token_address, balance_by_token_address


async def batched_rpc_requests(requests: List[dict], batch_size: int):
    tasks = []
    for i in range(0, len(requests), batch_size):
        batch = requests[i : i + batch_size]
        tasks.append(rpc_request(batch))

    results = await asyncio.gather(*tasks)
    return [
        item for sublist in results for item in sublist
    ]  # Flatten the list of lists
