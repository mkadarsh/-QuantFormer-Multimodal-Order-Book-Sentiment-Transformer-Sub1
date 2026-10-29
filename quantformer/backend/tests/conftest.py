"""
Pytest configuration and fixtures
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def test_market_data():
    """Sample market data for testing"""
    return {
        "symbol": "DEMO",
        "timestamp": "2024-01-01T10:00:00Z",
        "bids": [
            {"price": 500.20, "volume": 1200},
            {"price": 500.15, "volume": 950},
        ],
        "asks": [
            {"price": 500.30, "volume": 900},
            {"price": 500.35, "volume": 1500},
        ]
    }


@pytest.fixture
def test_sentiment_data():
    """Sample sentiment data for testing"""
    return {
        "headline": "Company reports record quarterly earnings",
        "sentiment": "positive",
        "score": 0.85,
        "timestamp": "2024-01-01T10:05:00Z"
    }
