from app.models.explainability import ExplainabilityService
from app.models.predictor import PredictionService


def test_explanation_uses_signal_contribution_estimate():
    prediction = PredictionService().predict(
        {
            "symbol": "DEMO",
            "current_price": 100,
            "normalized_score": -0.8,
            "order_book_imbalance": -0.6,
            "price_change_pct": -0.01,
            "liquidity_score": 20,
        }
    )
    explanation = ExplainabilityService().explain_prediction(
        prediction,
        {
            "order_book_imbalance": -0.6,
            "price_momentum": -0.01,
            "liquidity_score": 20,
        },
        {"normalized_score": -0.8},
    )
    assert explanation["label"] == "Signal Contribution Estimate"
    assert explanation["prediction"] == prediction
    assert explanation["risk_level"] == prediction["risk_level"]
    assert set(explanation["feature_contributions"]) == {
        "news_sentiment",
        "order_book_imbalance",
        "price_momentum",
        "liquidity",
    }
    assert "influenced" in explanation["human_readable_explanation"]

