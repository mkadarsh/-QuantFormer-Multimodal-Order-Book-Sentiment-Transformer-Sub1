"""Unit tests for the FinBERT sentiment service."""

from unittest.mock import patch

import pytest

from app.news.sentiment import FinBERTSentimentService


def test_sentiment_normalization():
    assert FinBERTSentimentService.normalize_score("positive", 0.85) == pytest.approx(0.85)
    assert FinBERTSentimentService.normalize_score("negative", 0.85) == pytest.approx(-0.85)
    assert FinBERTSentimentService.normalize_score("neutral", 0.85) == 0.0


def test_sentiment_normalization_rejects_unknown_label():
    with pytest.raises(ValueError):
        FinBERTSentimentService.normalize_score("unknown", 0.5)


def test_invalid_news_is_rejected():
    service = object.__new__(FinBERTSentimentService)
    with pytest.raises(ValueError):
        service.process_news({"id": "news-1", "headline": "  "})


def test_output_schema():
    service = object.__new__(FinBERTSentimentService)
    service.analyze = lambda headline: {
        "sentiment": "positive",
        "score": 0.85,
        "normalized_score": 0.85,
        "embedding": [0.1, 0.2],
    }
    output = service.process_news(
        {
            "id": "news-1",
            "symbol": "DEMO",
            "timestamp": "2026-08-31T12:00:00Z",
            "headline": "Revenue exceeds expectations",
        }
    )
    assert set(output) == {
        "news_id",
        "symbol",
        "timestamp",
        "headline",
        "sentiment",
        "score",
        "normalized_score",
        "embedding",
    }
    assert output["news_id"] == "news-1"
    assert output["normalized_score"] == 0.85


def test_service_initialization_loads_model_once():
    with patch.object(FinBERTSentimentService, "_load_model") as load_model:
        service = FinBERTSentimentService(device="cpu")
        load_model.assert_called_once_with()
        assert service.device == "cpu"
