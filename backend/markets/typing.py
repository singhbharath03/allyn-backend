from typing import Any, List, Optional
from pydantic import BaseModel


class CreateAttentionMarketRequest(BaseModel):
    slug: str
    image_url: str


class CreateAttentionMarketResponse(BaseModel):
    id: int
    slug: str
    image_url: str
    address: str
