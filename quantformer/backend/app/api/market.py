"""
API endpoints for market data
"""
from fastapi import APIRouter, HTTPException
from app.schemas.market import MarketDataResponse, OrderBookResponse

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/latest", response_model=MarketDataResponse)
async def get_latest_market_data():
    """Get latest market data"""
    # TODO: Implement in Phase 2
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/orderbook", response_model=OrderBookResponse)
async def get_orderbook():
    """Get current order book"""
    # TODO: Implement in Phase 2
    raise HTTPException(status_code=501, detail="Not implemented yet")
