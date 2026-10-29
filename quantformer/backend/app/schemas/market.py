"""
Pydantic schemas for market data validation and serialization
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class BidAskLevel(BaseModel):
    """Bid/Ask level in order book"""
    price: float = Field(..., description="Price level")
    volume: float = Field(..., gt=0, description="Volume at this level")


class MarketTick(BaseModel):
    """Single market tick with L2 order book"""
    symbol: str
    timestamp: datetime
    last_price: float = Field(..., gt=0, description="Last trade price")
    bid_price: float = Field(..., gt=0, description="Best bid price")
    ask_price: float = Field(..., gt=0, description="Best ask price")
    bids: List[BidAskLevel] = Field(..., description="Bid levels")
    asks: List[BidAskLevel] = Field(..., description="Ask levels")


class OrderBookResponse(BaseModel):
    """Order book data response"""
    symbol: str
    timestamp: datetime
    last_price: float
    bids: List[BidAskLevel]
    asks: List[BidAskLevel]
    bid_volume_total: float
    ask_volume_total: float
    spread: float


class MarketDataResponse(BaseModel):
    """Market data response"""
    symbol: str
    timestamp: datetime
    last_price: float
    bid: float
    ask: float
    volume: float
    price_change: float
    price_change_pct: float


class NewsResponse(BaseModel):
    """News headline response"""
    id: str
    timestamp: datetime
    headline: str
    source: str
    symbol: str
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None


class PredictionResponse(BaseModel):
    """Prediction response"""
    symbol: str
    timestamp: datetime
    current_price: float
    predicted_price: float
    direction: str  # UP, DOWN, NEUTRAL
    confidence: float
    lower_bound: float
    upper_bound: float
    risk_level: Optional[str] = None


class SentimentResponse(BaseModel):
    symbol: str
    timestamp: datetime
    sentiment: str
    score: float = Field(..., ge=0, le=1)
    normalized_score: float = Field(..., ge=-1, le=1)
    headline: Optional[str] = None
