"""
Kafka consumer for subscribing to market and news topics
"""
import logging
import json
from typing import Any, Iterable, Optional
from kafka import KafkaConsumer
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class KafkaConsumerService:
    """Small JSON Kafka consumer wrapper with explicit unavailable state."""

    def __init__(
        self,
        topics: Iterable[str],
        bootstrap_servers: Optional[str] = None,
        group_id: str = "quantformer",
    ) -> None:
        self.topics = list(topics)
        self.group_id = group_id
        try:
            self.consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=group_id,
                auto_offset_reset="latest",
            )
        except Exception as exc:
            logger.error("Failed to initialize Kafka consumer: %s", exc)
            self.consumer = None

    @staticmethod
    def _deserialize_json(data: Optional[bytes]) -> Any:
        if data is None:
            return None
        try:
            return json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
            raise ValueError("Unable to deserialize Kafka payload") from exc

    def close(self) -> None:
        if self.consumer is not None:
            self.consumer.close()

    def __enter__(self) -> "KafkaConsumerService":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class MarketDataConsumer(KafkaConsumerService):
    def __init__(
        self,
        group_id: str = "market-processor",
        bootstrap_servers: Optional[str] = None,
    ) -> None:
        super().__init__(
            topics=[settings.KAFKA_TOPIC_MARKET_DATA],
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
        )
