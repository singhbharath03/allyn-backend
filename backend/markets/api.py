import logging

from markets.models import AttentionMarket
from markets.client import get_sonic_testnet_client
from markets.constants import DEFAULT_DECIMALS
from markets.keypair import get_keypair
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import get_associated_token_address

logger = logging.getLogger(__name__)


async def create_attention_market(slug: str, image_url: str) -> AttentionMarket:
    token_address = await create_and_mint_token()

    # create a new attention market
    market = await AttentionMarket.objects.acreate(
        slug=slug, image_url=image_url, address=token_address
    )

    return market


async def create_and_mint_token() -> str:
    # create a new token
    client = await get_sonic_testnet_client()
    token_client = await AsyncToken.create_mint(
        client,
        get_keypair(),
        get_keypair().pubkey(),
        DEFAULT_DECIMALS,
        TOKEN_PROGRAM_ID,
    )

    logger.info("Created mint: %s", token_client.pubkey)

    # Get the associated token account address
    associated_token_account = get_associated_token_address(
        owner=get_keypair().pubkey(), mint=token_client.pubkey
    )

    logger.info("Associated token account: %s", associated_token_account)

    # Create associated token account if it doesn't exist
    await token_client.create_associated_token_account(owner=get_keypair().pubkey())

    logger.info("Created associated token account")

    # mint 100_000_000 tokens to the associated token account
    await token_client.mint_to(
        dest=associated_token_account,
        mint_authority=get_keypair().pubkey(),
        amount=100_000_000,
        multi_signers=[get_keypair()],
    )

    logger.info("Minted tokens successfully")

    return token_client.pubkey
