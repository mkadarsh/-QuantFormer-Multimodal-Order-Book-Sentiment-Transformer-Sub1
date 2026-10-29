"""
Generate mock financial news data and stream it to Kafka.
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

from kafka import KafkaProducer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.news.simulator import NewsSimulator

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_producer():
    """Create a Kafka producer configured for JSON payloads."""
    return KafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value, default=str).encode("utf-8"),
    )


def generate_news_batch(symbol: str = "DEMO", count: int = 5):
    """Generate a batch of mock news events."""
    simulator = NewsSimulator(symbols=[symbol], source="MockNewsGenerator")
    items = []
    for _ in range(count):
        items.append(simulator.generate_news(symbol=symbol))
    return items


def stream_news(symbol: str = "DEMO", interval_seconds: int = 5, topic: str = None):
    """Stream news messages to Kafka until interrupted."""
    topic = topic or settings.KAFKA_TOPIC_NEWS_DATA
    simulator = NewsSimulator(
        symbols=[symbol],
        source="KafkaNewsProducer",
        update_interval_seconds=interval_seconds,
    )

    try:
        producer = _build_producer()
        logger.info("Connected to Kafka bootstrap servers: %s", settings.KAFKA_BOOTSTRAP_SERVERS)
    except Exception as exc:  # pragma: no cover - depends on external Kafka
        logger.warning("Kafka not available (%s). Running in mock stream mode.", exc)
        producer = None

    try:
        while True:
            item = simulator.generate_news(symbol=symbol)
            if producer is not None:
                producer.send(topic, value=item)
                producer.flush()
                logger.info("Published news to %s: %s", topic, item["headline"])
            else:
                logger.info("Mock news stream: %s", item["headline"])
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        logger.info("News streaming stopped by user.")
    finally:
        if producer is not None:
            producer.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Generate mock financial news")
    parser.add_argument("--symbol", type=str, default="DEMO", help="Ticker symbol for generated news")
    parser.add_argument("--interval", type=int, default=5, help="Seconds between generated items")
    parser.add_argument("--count", type=int, default=5, help="Number of news items to generate in batch mode")
    parser.add_argument("--topic", type=str, default=settings.KAFKA_TOPIC_NEWS_DATA, help="Kafka topic")
    parser.add_argument("--stream", action="store_true", help="Continuously stream news to Kafka")
    args = parser.parse_args()

    if args.stream:
        stream_news(symbol=args.symbol, interval_seconds=args.interval, topic=args.topic)
    else:
        for item in generate_news_batch(symbol=args.symbol, count=args.count):
            print(json.dumps(item, default=str))
