import logging

from markets.api import create_attention_market as create_attention_market_api
from markets.typing import CreateAttentionMarketRequest, CreateAttentionMarketResponse
from fastapi import APIRouter, Request, FastAPI, HTTPException


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/test/")
async def test(request: Request):
    return {"message": "Hello, World!"}


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
