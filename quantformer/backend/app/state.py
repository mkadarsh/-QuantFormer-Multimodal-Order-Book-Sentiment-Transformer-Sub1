"""In-memory application state and asynchronous market stream."""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

from fastapi.encoders import jsonable_encoder
from app.market.simulator import MarketSimulator
from app.models.explainability import ExplainabilityService
from app.models.predictor import PredictionService
from app.news.simulator import NewsSimulator
from app.news.sentiment import FinBERTSentimentService
from app.kafka.consumer import KafkaConsumerService
from app.schemas.market import MarketTick
from app.schemas.news import NewsItem

logger = logging.getLogger(__name__)


class AppState:
    """MVP cache shared by REST handlers and WebSocket clients."""

    def __init__(
        self,
        symbol: str = "DEMO",
        initial_price: float = 500.25,
        model_mode: str = "mock",
        model_path: str | None = None,
        model_fallback: bool = False,
        prediction_interval_seconds: float = 1.0,
        sentiment_mode: str = "finbert",
        device: str = "cpu",
        kafka_enabled: bool = False,
    ) -> None:
        self.symbol = symbol
        self.market_simulator = MarketSimulator(symbol, initial_price)
        self.news_simulator = NewsSimulator(symbols=[symbol])
        self.predictor = PredictionService(
            model_mode=model_mode,
            model_path=model_path,
            model_fallback=model_fallback,
        )
        self.prediction_interval_seconds = max(0.1, prediction_interval_seconds)
        self.sentiment_mode = sentiment_mode
        self.device = device
        self.sentiment_service: FinBERTSentimentService | None = None
        self.sentiment_error: str | None = None
        self._last_prediction_at = 0.0
        self._next_news_at = time.monotonic() + self.news_simulator.update_interval_seconds
        self._previous_price = initial_price
        self.explainer = ExplainabilityService()
        self.market: dict[str, Any] | None = None
        self.orderbook: dict[str, Any] | None = None
        self.news: dict[str, Any] | None = None
        self.sentiment: dict[str, Any] | None = None
        self.prediction: dict[str, Any] | None = None
        self.history: list[dict[str, Any]] = []
        self.clients: set[asyncio.Queue[dict[str, Any]]] = set()
        self.kafka_status = "unavailable"
        self.market_consumer: KafkaConsumerService | None = None
        self.news_consumer: KafkaConsumerService | None = None
        if kafka_enabled:
            from app.config import get_settings
            kafka_settings = get_settings()
            self.market_consumer = KafkaConsumerService(
                [kafka_settings.KAFKA_TOPIC_MARKET_DATA],
                group_id="quantformer-market",
            )
            self.news_consumer = KafkaConsumerService(
                [kafka_settings.KAFKA_TOPIC_SENTIMENT_DATA, kafka_settings.KAFKA_TOPIC_NEWS_DATA],
                group_id="quantformer-news",
            )
            if self.market_consumer.consumer or self.news_consumer.consumer:
                self.kafka_status = "connected"
        self._seed()

    def _seed(self) -> None:
        self.update_market(self.market_simulator.generate_tick())
        self.update_news(self.news_simulator.generate_news(self.symbol), analyze_sentiment=False)
        self._refresh_prediction(force=True)

    def update_market(self, tick: dict[str, Any]) -> None:
        validated = MarketTick.model_validate(tick)
        previous_price = float(self.market["last_price"]) if self.market else validated.last_price
        price_change = validated.last_price - previous_price
        price_change_pct = price_change / previous_price if previous_price else 0.0
        sentiment_score = self._as_of_sentiment(validated.timestamp)
        self.market = {
            "symbol": validated.symbol,
            "timestamp": validated.timestamp,
            "last_price": validated.last_price,
            "bid": validated.bid_price,
            "ask": validated.ask_price,
            "volume": sum(level.volume for level in validated.bids + validated.asks),
            "price_change": price_change,
            "price_change_pct": price_change_pct,
        }
        self.orderbook = {
            "symbol": validated.symbol,
            "timestamp": validated.timestamp,
            "last_price": validated.last_price,
            "bids": validated.bids,
            "asks": validated.asks,
            "bid_volume_total": sum(level.volume for level in validated.bids),
            "ask_volume_total": sum(level.volume for level in validated.asks),
            "spread": validated.ask_price - validated.bid_price,
        }
        features = {
            "symbol": validated.symbol,
            "timestamp": validated.timestamp,
            "current_price": validated.last_price,
            "price_momentum": price_change_pct,
            "order_book_imbalance": (
                (self.orderbook["bid_volume_total"] - self.orderbook["ask_volume_total"])
                / max(self.orderbook["bid_volume_total"] + self.orderbook["ask_volume_total"], 1)
            ),
            "liquidity_score": min(
                100.0, (self.orderbook["bid_volume_total"] + self.orderbook["ask_volume_total"]) / 20
            ),
            "sentiment_score": sentiment_score,
            "normalized_score": sentiment_score,
        }
        self._features = features
        self._previous_price = validated.last_price
        self.history.append(dict(self.market))
        self.history = self.history[-100:]

    def update_news(self, item: dict[str, Any], analyze_sentiment: bool = True) -> None:
        validated = NewsItem.model_validate(item)
        self.news = validated.model_dump(mode="json")
        label = self.news_simulator.get_sentiment_type(validated.headline)
        score = {"positive": 0.75, "negative": -0.75, "neutral": 0.0}[label]
        if analyze_sentiment and self.sentiment_mode == "finbert":
            try:
                if self.sentiment_service is None:
                    self.sentiment_service = FinBERTSentimentService(device=self.device)
                result = self.sentiment_service.analyze(validated.headline)
                label = result["sentiment"]
                score = float(result["normalized_score"])
                self.sentiment_error = None
            except (RuntimeError, ValueError) as exc:
                self.sentiment_error = str(exc)
                logger.warning("FinBERT unavailable; retaining simulator sentiment: %s", exc)
        self.sentiment = {
            "symbol": validated.symbol,
            "timestamp": validated.timestamp,
            "sentiment": label,
            "score": abs(score),
            "normalized_score": score,
            "headline": validated.headline,
            "source": "finbert" if analyze_sentiment and self.sentiment_error is None and self.sentiment_mode == "finbert" else "fallback",
        }
        if self.market:
            self._features["sentiment_score"] = score
            self._features["normalized_score"] = score

    def _as_of_sentiment(self, market_timestamp: Any) -> float:
        """Use only sentiment that existed at or before the market observation."""
        if not self.sentiment:
            return 0.0
        try:
            market_time = datetime.fromisoformat(str(market_timestamp).replace("Z", "+00:00"))
            sentiment_time = datetime.fromisoformat(
                str(self.sentiment["timestamp"]).replace("Z", "+00:00")
            )
        except (TypeError, ValueError):
            return 0.0
        if market_time.tzinfo is None and sentiment_time.tzinfo is not None:
            market_time = market_time.replace(tzinfo=timezone.utc)
        elif sentiment_time.tzinfo is None and market_time.tzinfo is not None:
            sentiment_time = sentiment_time.replace(tzinfo=timezone.utc)
        return float(self.sentiment["normalized_score"]) if sentiment_time <= market_time else 0.0

    def _refresh_prediction(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self._last_prediction_at < self.prediction_interval_seconds:
            return
        try:
            self.prediction = self.predictor.predict(self._features)
            self._last_prediction_at = now
        except RuntimeError as exc:
            self.prediction = None
            self.predictor.model_error = str(exc)
            logger.error("Prediction unavailable: %s", exc)

    def snapshot(self) -> dict[str, Any]:
        return jsonable_encoder({
            "type": "market",
            "timestamp": datetime.now(timezone.utc),
            "market": self.market,
            "orderbook": self.orderbook,
            "news": self.news,
            "sentiment": self.sentiment,
            "prediction": self.prediction,
            "model": self.predictor.status,
            "sentiment_status": {
                "model": "FINBERT",
                "loaded": self.sentiment_service is not None and self.sentiment_service.model is not None,
                "error": self.sentiment_error,
            },
        })

    async def publish(self, payload: dict[str, Any]) -> None:
        for queue in tuple(self.clients):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning("Dropping stale WebSocket update for a slow client")

    async def run(self, interval_ms: int) -> None:
        while True:
            await asyncio.sleep(max(interval_ms, 10) / 1000)
            kafka_market = await self._poll(self.market_consumer)
            if kafka_market:
                self.update_market(kafka_market)
            else:
                self.update_market(self.market_simulator.generate_tick())
            kafka_news = await self._poll(self.news_consumer)
            if kafka_news:
                for event in kafka_news:
                    if "headline" in event:
                        self.update_news(event)
            self._refresh_prediction()
            if time.monotonic() >= self._next_news_at:
                await asyncio.to_thread(
                    self.update_news,
                    self.news_simulator.generate_news(self.symbol),
                )
                self._next_news_at = time.monotonic() + self.news_simulator.update_interval_seconds
            await self.publish(self.snapshot())

    @staticmethod
    async def _poll(consumer: KafkaConsumerService | None) -> list[dict[str, Any]]:
        if consumer is None or consumer.consumer is None:
            return []
        records = await asyncio.to_thread(consumer.consumer.poll, timeout_ms=10, max_records=10)
        return [
            value
            for messages in records.values()
            for message in messages
            if isinstance((value := consumer._deserialize_json(message.value)), dict)
        ]

    def explanation(self) -> dict[str, Any]:
        if not self.prediction or not self.market or not self.sentiment:
            return {"status": "unavailable", "message": "Prediction explanation is unavailable"}
        features = {
            "order_book_imbalance": (
                self.orderbook["bid_volume_total"] - self.orderbook["ask_volume_total"]
            ) / max(self.orderbook["bid_volume_total"] + self.orderbook["ask_volume_total"], 1),
            "price_momentum": 0.0,
            "liquidity_score": min(
                100.0, (self.orderbook["bid_volume_total"] + self.orderbook["ask_volume_total"]) / 20
            ),
        }
        return self.explainer.explain_prediction(self.prediction, features, self.sentiment)
