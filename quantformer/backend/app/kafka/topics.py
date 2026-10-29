"""
Kafka topic definitions and initialization
"""
from app.config import get_settings

settings = get_settings()

# Define Kafka topics
TOPICS = {
    "market_data": settings.KAFKA_TOPIC_MARKET_DATA,
    "news_data": settings.KAFKA_TOPIC_NEWS_DATA,
    "sentiment_data": settings.KAFKA_TOPIC_SENTIMENT_DATA,
    "prediction_data": settings.KAFKA_TOPIC_PREDICTION_DATA,
}


def get_topic(key: str) -> str:
    """Get topic name by key"""
    return TOPICS.get(key, key)


def get_all_topics() -> list[str]:
    """Return configured topic names without exposing the mapping."""
    return list(TOPICS.values())


def initialize_topics():
    """Initialize Kafka topics (auto-create if enabled)"""
    # TODO: Implement topic creation logic in Phase 3
    # Kafka is configured with auto.create.topics.enable=true in docker-compose
    pass
