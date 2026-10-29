"""Tests for the mock news simulator."""
import json
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.news.simulator import NewsSimulator
from app.schemas.news import NewsItem


class TestNewsItem:
    """Validate news item schema constraints."""

    def test_news_item_validates(self):
        """News items should validate with a valid structure."""
        item = NewsItem(
            id="news-001",
            timestamp=datetime.utcnow(),
            symbol="AAPL",
            headline="Company reports record quarterly earnings",
            source="Reuters",
        )

        assert item.id == "news-001"
        assert item.symbol == "AAPL"
        assert item.headline == "Company reports record quarterly earnings"
        assert isinstance(item.timestamp, datetime)

    def test_news_item_rejects_invalid_symbol(self):
        """Symbols must be uppercase ticker-like values."""
        with pytest.raises(ValidationError):
            NewsItem(
                id="news-002",
                timestamp=datetime.utcnow(),
                symbol="aapl!",
                headline="Company announces quarterly results",
                source="CNBC",
            )

    def test_news_item_rejects_empty_headline(self):
        """Headlines cannot be blank."""
        with pytest.raises(ValidationError):
            NewsItem(
                id="news-003",
                timestamp=datetime.utcnow(),
                symbol="MSFT",
                headline="   ",
                source="Bloomberg",
            )

    def test_kafka_serialization(self):
        """Messages should serialize cleanly to JSON bytes for Kafka."""
        item = NewsItem(
            id="news-004",
            timestamp=datetime.utcnow(),
            symbol="NVDA",
            headline="Company receives major new contract",
            source="AP",
        )

        payload = json.dumps(item.model_dump(mode="json"), default=str).encode("utf-8")
        decoded = json.loads(payload.decode("utf-8"))

        assert decoded["symbol"] == "NVDA"
        assert decoded["headline"] == "Company receives major new contract"
        assert "timestamp" in decoded


class TestNewsSimulator:
    """Validate the news stream simulator."""

    def test_generate_news_promotes_valid_data(self):
        """Generator should produce realistic, valid items."""
        simulator = NewsSimulator(symbols=["AAPL", "MSFT"], source="MarketWire")
        item = simulator.generate_news()

        assert item["symbol"] in {"AAPL", "MSFT"}
        assert item["headline"]
        assert item["source"] == "MarketWire"
        assert isinstance(item["timestamp"], str)
