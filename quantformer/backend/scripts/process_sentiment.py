"""Consume news-data, run FinBERT, and publish sentiment-data."""

import argparse
import json
import logging
import sys
from pathlib import Path

from kafka import KafkaConsumer, KafkaProducer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.news.sentiment import FinBERTSentimentService

logger = logging.getLogger(__name__)


def _deserialize(value: bytes):
    """Turn malformed Kafka payloads into events the worker can skip."""
    try:
        return json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.warning("Skipping invalid Kafka JSON payload: %s", exc)
        return None


def process_sentiment(
    bootstrap_servers: str | None = None,
    input_topic: str | None = None,
    output_topic: str | None = None,
    group_id: str = "finbert-sentiment-processor",
) -> None:
    """Run the Kafka sentiment worker until interrupted."""
    settings = get_settings()
    bootstrap_servers = bootstrap_servers or settings.KAFKA_BOOTSTRAP_SERVERS
    input_topic = input_topic or settings.KAFKA_TOPIC_NEWS_DATA
    output_topic = output_topic or settings.KAFKA_TOPIC_SENTIMENT_DATA
    service = FinBERTSentimentService()
    consumer = None
    producer = None
    try:
        consumer = KafkaConsumer(
            input_topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            auto_offset_reset="latest",
            value_deserializer=_deserialize,
        )
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
        )
        logger.info("Processing %s with FinBERT; publishing to %s", input_topic, output_topic)
        for message in consumer:
            try:
                result = service.process_news(message.value)
                producer.send(output_topic, value=result)
                producer.flush()
                logger.info(
                    "%s -> FinBERT -> %s (%.3f)",
                    result["headline"],
                    result["sentiment"],
                    result["score"],
                )
            except (ValueError, RuntimeError, TypeError, KeyError):
                logger.exception("Skipping malformed or failed news message")
    except Exception:
        logger.exception("Kafka sentiment processor failed")
        raise
    finally:
        if consumer is not None:
            consumer.close()
        if producer is not None:
            producer.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Process news headlines with FinBERT")
    parser.add_argument("--group-id", default="finbert-sentiment-processor")
    args = parser.parse_args()
    try:
        process_sentiment(group_id=args.group_id)
    except KeyboardInterrupt:
        logger.info("Sentiment processing stopped by user.")
