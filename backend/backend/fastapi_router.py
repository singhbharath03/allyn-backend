from fastapi import FastAPI
from markets.views import router as market_router


def setup_routers(app: FastAPI):
    """Routes"""
    app.include_router(market_router, prefix="/markets")
