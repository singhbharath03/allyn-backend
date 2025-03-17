import logging
from typing import List

from markets.models import AttentionMarket
from markets.token_trades import get_sol_token_trades
from markets.api import (
    create_attention_market as create_attention_market_api,
    get_attention_markets as get_attention_markets_api,
)
from markets.typing import (
    CreateAttentionMarketRequest,
    CreateAttentionMarketResponse,
    TokenTrade,
)
from fastapi import APIRouter, Request, FastAPI, HTTPException


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/attention/")
async def create_attention_market(
    request: CreateAttentionMarketRequest,
) -> CreateAttentionMarketResponse:
    market = await create_attention_market_api(request.slug, request.image_url)

    return CreateAttentionMarketResponse(
        id=market.id,
        slug=market.slug,
        image_url=market.image_url,
        address=market.address,
    )


@router.get("/attention/")
async def get_attention_markets(
    request: Request,
) -> List[CreateAttentionMarketResponse]:
    return await get_attention_markets_api()


@router.get("/attention/trades/{market_id}")
async def get_attention_market_trades(
    market_id: int,
) -> List[TokenTrade]:
    market = await AttentionMarket.objects.aget(id=market_id)
    trades = await get_sol_token_trades(market.address)
    return trades
