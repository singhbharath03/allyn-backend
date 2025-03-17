from markets.typing import TokenTrade
from markets.rpc import get_all_signatures, get_transactions
from typing import Dict, Any, Optional, List


async def get_sol_token_trades(token_address: str) -> List[TokenTrade]:
    """
    Gets the history of SOL/token trades for a specific token.

    Args:
        token_address: Address of the token

    Returns:
        List of trade details objects
    """
    signatures = await get_all_signatures(token_address)
    transactions = await get_transactions(signatures)

    sol_trades = []
    for tx in transactions:
        trade_info = is_sol_token_trade(tx)
        if trade_info:
            sol_trades.append(trade_info)

    return sol_trades


def is_sol_token_trade(transaction: Dict[str, Any]) -> Optional[TokenTrade]:
    """
    Identifies if a transaction is a buy/sell with native SOL token.
    Checks signer's balance changes to determine if SOL was exchanged for tokens.

    Args:
        transaction: A transaction object from the Solana blockchain

    Returns:
        Dictionary with trade details if it's a SOL trade, None otherwise
    """
    # Basic validation
    if not transaction or "meta" not in transaction or "transaction" not in transaction:
        return None

    meta = transaction["meta"]
    tx_message = transaction["transaction"]["message"]

    # Get signers (first account in accountKeys is usually the signer/fee payer)
    account_keys = tx_message.get("accountKeys", [])
    if not account_keys:
        return None

    # Find the signer account
    signers = [acc for acc in account_keys if acc.get("signer")]
    if not signers:
        return None

    signer = signers[0]["pubkey"]
    signer_index = next(
        (i for i, acc in enumerate(account_keys) if acc.get("pubkey") == signer), None
    )
    if signer_index is None:
        return None

    # Get SOL balances before and after
    pre_sol_balance = (
        meta.get("preBalances", [])[signer_index]
        if signer_index < len(meta.get("preBalances", []))
        else 0
    )
    post_sol_balance = (
        meta.get("postBalances", [])[signer_index]
        if signer_index < len(meta.get("postBalances", []))
        else 0
    )
    sol_change = (post_sol_balance - pre_sol_balance) / 10**9  # Convert lamports to SOL

    # Get token balances before and after
    pre_token_balances = meta.get("preTokenBalances", [])
    post_token_balances = meta.get("postTokenBalances", [])

    # Find tokens owned by the signer
    signer_pre_tokens = {
        balance["mint"]: float(balance["uiTokenAmount"]["amount"])
        / 10 ** balance["uiTokenAmount"]["decimals"]
        for balance in pre_token_balances
        if balance.get("owner") == signer
    }

    signer_post_tokens = {
        balance["mint"]: float(balance["uiTokenAmount"]["amount"])
        / 10 ** balance["uiTokenAmount"]["decimals"]
        for balance in post_token_balances
        if balance.get("owner") == signer
    }

    # Calculate token changes
    token_changes = {}
    all_tokens = set(list(signer_pre_tokens.keys()) + list(signer_post_tokens.keys()))

    for token in all_tokens:
        pre_amount = signer_pre_tokens.get(token, 0)
        post_amount = signer_post_tokens.get(token, 0)
        change = post_amount - pre_amount
        if change != 0:
            token_changes[token] = change

    # Transaction fee always reduces SOL balance, so we need to account for it
    transaction_fee = meta.get("fee", 0) / 10**9
    adjusted_sol_change = sol_change + transaction_fee

    # Determine if this is a buy or sell with SOL
    if adjusted_sol_change < 0 and any(change > 0 for change in token_changes.values()):
        # SOL decreased, token increased = BUY
        traded_token = next(
            (token for token, change in token_changes.items() if change > 0), None
        )
        return TokenTrade(
            type="buy",
            sol_amount=abs(adjusted_sol_change),
            token=traded_token,
            token_amount=token_changes.get(traded_token, 0) if traded_token else 0,
            timestamp=transaction.get("blockTime"),
            signature=(
                transaction["transaction"]["signatures"][0]
                if transaction["transaction"].get("signatures")
                else None
            ),
            signer=signer,
        )
    elif adjusted_sol_change > 0 and any(
        change < 0 for change in token_changes.values()
    ):
        # SOL increased, token decreased = SELL
        traded_token = next(
            (token for token, change in token_changes.items() if change < 0), None
        )
        return TokenTrade(
            type="sell",
            sol_amount=adjusted_sol_change,
            token=traded_token,
            token_amount=(
                abs(token_changes.get(traded_token, 0)) if traded_token else 0
            ),
            timestamp=transaction.get("blockTime"),
            signature=(
                transaction["transaction"]["signatures"][0]
                if transaction["transaction"].get("signatures")
                else None
            ),
            signer=signer,
        )

    return None
