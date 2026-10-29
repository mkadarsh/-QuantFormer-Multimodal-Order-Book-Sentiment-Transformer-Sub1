"""
Kafka producer for publishing market and news data
"""
import json
import logging
from typing import Any, Optional

from kafka import KafkaProducer

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class KafkaProducerService:
    """Small JSON Kafka producer wrapper used by the processing services."""

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> None:
        self.bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
        self.client_id = client_id
        try:
            kwargs: dict[str, Any] = {"bootstrap_servers": self.bootstrap_servers}
            if client_id:
                kwargs["client_id"] = client_id
            self.producer = KafkaProducer(
                value_serializer=self._serialize_json,
                **kwargs,
            )
        except Exception as exc:
            logger.error("Failed to initialize Kafka producer: %s", exc)
            self.producer = None

    @staticmethod
    def _serialize_json(data: Any) -> bytes:
        try:
            return json.dumps(data, default=str).encode("utf-8")
        except (TypeError, ValueError, RecursionError) as exc:
            raise ValueError("Unable to serialize Kafka payload") from exc

    def is_connected(self) -> bool:
        return self.producer is not None

    def publish(self, topic: str, data: dict) -> Optional[dict]:
        if self.producer is None:
            return None
        self.producer.send(topic, value=data)
        self.producer.flush()
        return data

    def close(self) -> None:
        if self.producer is not None:
            self.producer.close()

    def __enter__(self) -> "KafkaProducerService":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class MarketDataProducer:
    """Produces market data to Kafka."""

    def __init__(self):
        """Initialize Kafka producer."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            )
            logger.info(f"Kafka producer connected to {settings.KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as exc:
            logger.error(f"Failed to initialize Kafka producer: {exc}")
            self.producer = None

    def publish_market_data(self, topic: str, data: dict):
        """Publish market data to Kafka topic."""
        if not self.producer:
            logger.warning("Kafka producer unavailable; skipping market-data publish")
            return None
        self.producer.send(topic, value=data)
        self.producer.flush()
        return data

    def close(self):
        """Close producer connection."""
        if self.producer:
            self.producer.close()


class NewsDataProducer:
    """Produces news updates to Kafka."""

    def __init__(self):
        """Initialize Kafka producer."""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            )
            logger.info(f"Kafka producer connected to {settings.KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as exc:
            logger.error(f"Failed to initialize Kafka producer: {exc}")
            self.producer = None

    def publish_news_data(self, topic: str, data: dict):
        """Publish a news item to Kafka topic."""
        if not self.producer:
            logger.warning("Kafka producer unavailable; skipping news-data publish")
            return None
        self.producer.send(topic, value=data)
        self.producer.flush()
        return data

    def close(self):
        """Close producer connection."""
        if self.producer:
            self.producer.close()
