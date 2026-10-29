"""
API endpoints for news data
"""
from fastapi import APIRouter, HTTPException
from app.schemas.market import NewsResponse

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/latest", response_model=NewsResponse)
async def get_latest_news():
    """Get latest financial news"""
    # TODO: Implement in Phase 4
    raise HTTPException(status_code=501, detail="Not implemented yet")
