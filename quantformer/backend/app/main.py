"""QuantFormer REST and WebSocket API."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas.market import (
    MarketDataResponse,
    OrderBookResponse,
    PredictionResponse,
    SentimentResponse,
)
from app.schemas.news import NewsItem
from app.schemas.prediction import ExplanationResult
from app.state import AppState

settings = get_settings()
logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)
state = AppState(
    settings.MARKET_SYMBOLS[0],
    settings.MARKET_INITIAL_PRICE,
    settings.MODEL_MODE,
    settings.TFT_MODEL_PATH,
)
stream_task: asyncio.Task[None] | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global stream_task
    stream_task = asyncio.create_task(state.run(settings.MARKET_UPDATE_INTERVAL_MS))
    try:
        yield
    finally:
        stream_task.cancel()
        await asyncio.gather(stream_task, return_exceptions=True)


app = FastAPI(
    title="QuantFormer API",
    description="Multimodal Order Book & Sentiment Transformer",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _symbol(value: str | None) -> str:
    symbol = value or state.symbol
    if symbol.upper() != state.symbol.upper():
        raise HTTPException(status_code=404, detail=f"Unknown symbol: {symbol}")
    return state.symbol


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "quantformer",
        "kafka": state.kafka_status,
        "model": settings.MODEL_MODE,
    }


@app.get("/api/market/latest", response_model=MarketDataResponse)
async def market_latest(symbol: str | None = Query(default=None, min_length=1)) -> dict[str, Any]:
    _symbol(symbol)
    return state.market


@app.get("/api/orderbook", response_model=OrderBookResponse)
async def orderbook(symbol: str | None = Query(default=None, min_length=1)) -> dict[str, Any]:
    _symbol(symbol)
    return state.orderbook


@app.get("/api/news/latest", response_model=NewsItem)
async def news_latest(symbol: str | None = Query(default=None, min_length=1)) -> dict[str, Any]:
    _symbol(symbol)
    return state.news


@app.get("/api/sentiment/latest", response_model=SentimentResponse)
async def sentiment_latest(symbol: str | None = Query(default=None, min_length=1)) -> dict[str, Any]:
    _symbol(symbol)
    return state.sentiment


@app.get("/api/prediction/latest", response_model=PredictionResponse)
async def prediction_latest(symbol: str | None = Query(default=None, min_length=1)) -> dict[str, Any]:
    _symbol(symbol)
    if state.prediction is None:
        raise HTTPException(status_code=503, detail="Prediction is unavailable")
    return state.prediction


@app.get("/api/explanation")
async def explanation(symbol: str | None = Query(default=None, min_length=1)) -> dict[str, Any]:
    _symbol(symbol)
    return state.explanation()


@app.get("/api/history")
async def history(
    symbol: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> dict[str, Any]:
    _symbol(symbol)
    return {"symbol": state.symbol, "items": state.history[-limit:]}


@app.websocket("/ws/market")
async def market_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=10)
    state.clients.add(queue)
    try:
        await websocket.send_json(state.snapshot())
        while True:
            await websocket.send_json(await queue.get())
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    finally:
        state.clients.discard(queue)
