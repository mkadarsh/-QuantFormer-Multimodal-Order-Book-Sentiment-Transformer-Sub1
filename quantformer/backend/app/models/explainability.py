"""Prediction explanations and explicitly labelled signal estimates."""

from typing import Any, Dict


class ExplainabilityService:
    """Generate human-readable estimates, not TFT attention weights."""

    def explain_prediction(
        self, prediction: Dict[str, Any], features: Dict[str, Any], sentiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        sentiment_score = self._sentiment_signal(sentiment)
        imbalance = self._number(features, "order_book_imbalance")
        momentum = self._number(features, "price_momentum", self._number(features, "price_change_pct"))
        liquidity_score = self._number(features, "liquidity_score", 50.0)
        liquidity = 0.5 - (liquidity_score / 100.0 if liquidity_score > 1 else liquidity_score)
        contributions = {
            "news_sentiment": round(sentiment_score * 0.30, 4),
            "order_book_imbalance": round(imbalance * 0.25, 4),
            "price_momentum": round(momentum / 0.02 * 0.30, 4),
            "liquidity": round(liquidity * 0.15, 4),
        }
        negative = []
        if sentiment_score < -0.1:
            negative.append("negative news sentiment")
        if imbalance < -0.1:
            negative.append("selling pressure in the order book")
        if momentum < 0:
            negative.append("falling price momentum")
        if liquidity > 0.1:
            negative.append("declining bid-side liquidity")
        text = (
            "Prediction is influenced by " + self._join(negative) + "."
            if negative
            else "Prediction reflects balanced market signals with no dominant negative factor."
        )
        risk_level = prediction.get("risk_level", prediction.get("risk_signal", "NORMAL"))
        result = {
            "prediction": prediction,
            "risk_level": risk_level,
            "explanation_text": text,
            "human_readable_explanation": text,
            "feature_contributions": contributions,
            "risk_signal": risk_level,
            "label": "Signal Contribution Estimate",
        }
        if prediction.get("tft_attention") is not None:
            result["tft_attention"] = prediction["tft_attention"]
        return result

    def calculate_risk_signal(self, features: Dict, sentiment: Dict, prediction: Dict) -> str:
        from .predictor import PredictionService

        momentum = self._number(features, "price_momentum", self._number(features, "price_change_pct"))
        liquidity = self._number(features, "liquidity_score", 50.0)
        liquidity = 0.5 - (liquidity / 100.0 if liquidity > 1 else liquidity)
        return PredictionService._risk_signal(
            self._sentiment_signal(sentiment),
            self._number(features, "order_book_imbalance"),
            momentum / 0.02,
            liquidity,
            prediction.get("direction", "NEUTRAL"),
        )

    @staticmethod
    def _number(values: Dict[str, Any], key: str, default: float = 0.0) -> float:
        try:
            return float(values.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def _sentiment_signal(cls, sentiment: Dict[str, Any]) -> float:
        if "normalized_score" in sentiment:
            return max(-1.0, min(1.0, cls._number(sentiment, "normalized_score")))
        raw_score = cls._number(sentiment, "score", cls._number(sentiment, "sentiment_score"))
        if raw_score < 0:
            return max(-1.0, raw_score)
        score = min(1.0, raw_score)
        label = str(sentiment.get("sentiment", "neutral")).lower()
        return score if label == "positive" else -score if label == "negative" else 0.0

    @staticmethod
    def _join(items: list[str]) -> str:
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return ", ".join(items[:-1]) + f", and {items[-1]}"
