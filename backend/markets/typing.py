from typing import Any, List, Literal, Optional
from pydantic import BaseModel


class CreateAttentionMarketRequest(BaseModel):
    slug: str
    image_url: str


class CreateAttentionMarketResponse(BaseModel):
    id: int
    slug: str
    image_url: str
    address: str


class TokenTrade(BaseModel):
    type: Literal["buy", "sell"]
    sol_amount: float
    token: str
    token_amount: float
    timestamp: int
    signature: str
    signer: str
