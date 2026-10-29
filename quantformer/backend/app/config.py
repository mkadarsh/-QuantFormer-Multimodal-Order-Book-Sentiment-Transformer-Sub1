"""
Application configuration using environment variables
"""
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings from environment variables"""
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
    )
    KAFKA_TOPIC_MARKET_DATA: str = os.getenv(
        "KAFKA_TOPIC_MARKET_DATA", "market-data"
    )
    KAFKA_TOPIC_NEWS_DATA: str = os.getenv(
        "KAFKA_TOPIC_NEWS_DATA", "news-data"
    )
    KAFKA_TOPIC_SENTIMENT_DATA: str = os.getenv(
        "KAFKA_TOPIC_SENTIMENT_DATA", "sentiment-data"
    )
    KAFKA_TOPIC_PREDICTION_DATA: str = os.getenv(
        "KAFKA_TOPIC_PREDICTION_DATA", "prediction-data"
    )
    KAFKA_ENABLED: bool = os.getenv("KAFKA_ENABLED", "false").lower() == "true"
    
    # Market Simulator
    MARKET_UPDATE_INTERVAL_MS: int = int(
        os.getenv("MARKET_UPDATE_INTERVAL_MS", "100")
    )
    MARKET_SYMBOLS: list = os.getenv("MARKET_SYMBOLS", "DEMO").split(",")
    MARKET_INITIAL_PRICE: float = float(
        os.getenv("MARKET_INITIAL_PRICE", "500.25")
    )
    
    # News Simulator
    NEWS_UPDATE_INTERVAL_SECONDS: int = int(
        os.getenv("NEWS_UPDATE_INTERVAL_SECONDS")
        if os.getenv("NEWS_UPDATE_INTERVAL_SECONDS") is not None
        else max(int(os.getenv("NEWS_UPDATE_INTERVAL_MS", "5000")) / 1000, 1)
    )
    NEWS_UPDATE_INTERVAL_MS: int = NEWS_UPDATE_INTERVAL_SECONDS * 1000
    NEWS_SYMBOLS: list = os.getenv("NEWS_SYMBOLS", os.getenv("NEWS_SYMBOL", "DEMO")).split(",")
    
    # Model Configuration
    MODEL_MODE: str = os.getenv("MODEL_MODE", "mock")  # mock or tft
    MODEL_FALLBACK: bool = os.getenv("MODEL_FALLBACK", "false").lower() == "true"
    PREDICTION_INTERVAL_SECONDS: float = float(
        os.getenv("PREDICTION_INTERVAL_SECONDS", "1")
    )
    TFT_MODEL_PATH: str = os.getenv(
        "TFT_MODEL_PATH", "models/tft_model.pt"
    )
    TFT_SCALER_PATH: str = os.getenv(
        "TFT_SCALER_PATH", "models/scaler.pkl"
    )
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info").lower()
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "true").lower() == "true"
    FRONTEND_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    
    # Device Configuration
    DEVICE: str = os.getenv("DEVICE", "cpu")  # cuda or cpu
    SENTIMENT_MODE: str = os.getenv("SENTIMENT_MODE", "finbert").lower()
    
    # Paths
    TRANSFORMERS_CACHE: str = os.getenv(
        "TRANSFORMERS_CACHE", "./models/transformers_cache"
    )
    HF_HOME: str = os.getenv("HF_HOME", "./models")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
