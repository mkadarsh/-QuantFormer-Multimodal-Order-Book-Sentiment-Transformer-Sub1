"""
API endpoints for predictions
"""
from fastapi import APIRouter, HTTPException
from app.schemas.market import PredictionResponse

router = APIRouter(prefix="/api/prediction", tags=["predictions"])


@router.get("/latest", response_model=PredictionResponse)
async def get_latest_prediction():
    """Get latest market prediction"""
    # TODO: Implement in Phase 7
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/explanation")
async def get_explanation():
    """Get prediction explanation"""
    # TODO: Implement in Phase 14
    raise HTTPException(status_code=501, detail="Not implemented yet")
