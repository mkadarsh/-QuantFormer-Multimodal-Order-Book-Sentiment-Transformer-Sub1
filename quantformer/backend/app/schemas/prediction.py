"""
Pydantic schemas for prediction data
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class PredictionRequest(BaseModel):
    """Prediction request"""
    symbol: str


class PredictionResult(BaseModel):
    """Prediction result"""
    symbol: str
    timestamp: datetime
    current_price: float
    predicted_price: float
    confidence: float
    direction: str  # UP, DOWN, NEUTRAL


class ExplanationResult(BaseModel):
    """Prediction explanation"""
    prediction: Dict[str, Any]
    risk_level: str
    feature_contributions: Dict[str, float]
    human_readable_explanation: str
    label: str = "Signal Contribution Estimate"
    explanation_text: Optional[str] = None
    risk_signal: Optional[str] = None
    tft_attention: Optional[Dict[str, float]] = None
