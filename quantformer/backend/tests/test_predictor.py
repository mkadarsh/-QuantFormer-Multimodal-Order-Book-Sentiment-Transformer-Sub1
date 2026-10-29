"""Tests for the Phase 7 mock prediction engine."""

from app.models.explainability import ExplainabilityService
from app.models.predictor import PredictionService


def _features(**overrides):
    values = {
        "symbol": "DEMO",
        "timestamp": "2024-01-01T10:00:00Z",
        "current_price": 500.25,
        "price_momentum": 0.0,
        "sentiment_score": 0.0,
        "order_book_imbalance": 0.0,
        "liquidity_score": 50.0,
    }
    values.update(overrides)
    return values


def test_prediction_directions():
    service = PredictionService()
    assert service.predict(_features(price_momentum=0.02))["direction"] == "UP"
    assert service.predict(_features(price_momentum=-0.02))["direction"] == "DOWN"
    assert service.predict(_features())["direction"] == "NEUTRAL"


def test_risk_levels():
    service = PredictionService()
    assert service.predict(_features())["risk_signal"] == "NORMAL"
    assert service.predict(
        _features(sentiment_score=0.9, sentiment="negative", order_book_imbalance=-0.8)
    )["risk_signal"] == "WATCH"
    assert service.predict(
        _features(
            sentiment_score=0.9,
            sentiment="negative",
            order_book_imbalance=-0.8,
            price_momentum=-0.03,
            liquidity_score=5,
        )
    )["risk_signal"] == "HIGH_RISK"


def test_prediction_formatting_is_deterministic():
    result = PredictionService().predict(_features(sentiment_score=0.8, sentiment="positive"))
    assert result["symbol"] == "DEMO"
    assert result["timestamp"].endswith("Z")
    assert result["current_price"] == 500.25
    assert result["lower_bound"] <= result["predicted_price"] <= result["upper_bound"]
    assert 0.0 <= result["confidence"] <= 0.99


def test_explanation_contains_signal_contribution_estimate():
    prediction = PredictionService().predict(
        _features(sentiment_score=0.9, sentiment="negative", liquidity_score=10)
    )
    explanation = ExplainabilityService().explain_prediction(
        prediction, _features(order_book_imbalance=-0.5, liquidity_score=10), 
        {"sentiment": "negative", "score": 0.9},
    )
    assert explanation["label"] == "Signal Contribution Estimate"
    assert set(explanation["feature_contributions"]) == {
        "news_sentiment", "order_book_imbalance", "price_momentum", "liquidity",
    }
    assert "negative news sentiment" in explanation["explanation_text"]
