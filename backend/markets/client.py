from solana.rpc.async_api import AsyncClient


async def get_sonic_testnet_client():
    return AsyncClient("https://api.testnet.v1.sonic.game")
