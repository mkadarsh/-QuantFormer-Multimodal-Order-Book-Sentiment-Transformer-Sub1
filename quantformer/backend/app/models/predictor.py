"""Prediction service with the Phase 7 mock and Phase 10 TFT modes."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import torch

from .tft_model import FEATURE_COLUMNS, FORECAST_HORIZON, load_checkpoint


class PredictionService:
    """Generate predictions using either the deterministic mock or a trained TFT."""

    def __init__(
        self,
        model_mode: str = "mock",
        model_path: Optional[str] = None,
        model_fallback: bool = False,
        direction_threshold: float = 0.08,
        neutral_threshold: Optional[float] = None,
    ) -> None:
        self.model_mode = model_mode.lower()
        if self.model_mode not in {"mock", "tft"}:
            raise ValueError("model_mode must be either 'mock' or 'tft'")
        self.model = None
        self.model_fallback = model_fallback
        self.model_error: str | None = None
        self.model_loaded = self.model_mode == "mock"
        self._checkpoint: dict[str, Any] | None = None
        self._history: dict[str, deque[dict[str, Any]]] = defaultdict(lambda: deque(maxlen=128))
        self.direction_threshold = abs(float(direction_threshold))
        self.neutral_threshold = (
            self.direction_threshold if neutral_threshold is None else abs(float(neutral_threshold))
        )
        if self.model_mode == "tft":
            self._model_path = Path(model_path) if model_path else None
            if self._model_path is None:
                self.model_error = "TFT model path is not configured"
            elif not self._model_path.is_file():
                self.model_error = f"TFT model file was not found: {self._model_path}"

    @property
    def effective_model(self) -> str:
        return self.model_mode

    @property
    def status(self) -> dict[str, Any]:
        return {
            "model": self.effective_model.upper(),
            "loaded": self.model_loaded,
            "available": self.model_loaded,
            "error": self.model_error,
        }

    def _load_model(self, frame: pd.DataFrame) -> None:
        """Build the inference dataset from checkpoint metadata and load weights."""
        from pytorch_forecasting import TimeSeriesDataSet

        if self._model_path is None:
            raise RuntimeError(self.model_error or "TFT model path is not configured")
        if self.model is not None:
            return
        checkpoint = torch.load(self._model_path, map_location="cpu", weights_only=False)
        dataset = TimeSeriesDataSet.from_parameters(
            checkpoint["dataset_parameters"], frame, predict=True, stop_randomization=True
        )
        self.model, self._checkpoint = load_checkpoint(self._model_path, dataset)
        self.model_loaded = True
        self.model_error = None

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        if self.model_mode == "mock":
            return self._mock_predict(features)
        try:
            return self._tft_predict(features)
        except Exception as exc:
            self.model_loaded = False
            self.model_error = str(exc)
            if not self.model_fallback:
                raise RuntimeError("TFT model is unavailable") from exc
            self.model_mode = "mock"
            self.model_loaded = True
            return self._mock_predict(features)

    def _mock_predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(features, dict):
            raise ValueError("features must be an object")
        current_price = float(features.get("current_price", features.get("last_price", 0)))
        if current_price <= 0:
            raise ValueError("features must include a positive current_price")
        sentiment = self._sentiment_signal(features)
        momentum = self._momentum_signal(features, current_price)
        imbalance = max(-1.0, min(1.0, self._number(features, "order_book_imbalance")))
        liquidity = self._liquidity_signal(features)
        signal = sentiment * 0.30 + imbalance * 0.25 + momentum * 0.30 + liquidity * 0.15
        direction = self._direction(signal)
        confidence = round(min(0.99, 0.50 + abs(signal) * 0.49), 2)
        predicted_price = round(current_price * (1.0 + signal * 0.02), 2)
        uncertainty = max(current_price * 0.005, current_price * (1.0 - confidence) * 0.02)
        risk_signal = self._risk_signal(sentiment, imbalance, momentum, liquidity, direction)
        return {
            "symbol": str(features.get("symbol", "DEMO")),
            "timestamp": features.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "current_price": round(current_price, 2),
            "predicted_price": predicted_price,
            "direction": direction,
            "confidence": confidence,
            "lower_bound": round(max(0.01, predicted_price - uncertainty), 2),
            "upper_bound": round(predicted_price + uncertainty, 2),
            "risk_signal": risk_signal,
            "risk_level": risk_signal,
        }

    def _tft_predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(features, dict):
            raise ValueError("features must be an object")
        current_price = float(features.get("current_price", features.get("last_price", 0)))
        if current_price <= 0:
            raise ValueError("features must include a positive current_price")
        symbol = str(features.get("symbol", "DEMO"))
        row = {"price": current_price}
        aliases = {"total_bid_volume": "bid_volume_total", "total_ask_volume": "ask_volume_total"}
        for column in FEATURE_COLUMNS[1:]:
            row[column] = self._number(features, column, self._number(features, aliases.get(column, ""), 0.0))
        history = self._history[symbol]
        history.append(row)
        rows = list(history)
        while len(rows) < FORECAST_HORIZON + 12:
            rows.insert(0, dict(rows[0]))
        values = []
        for index, item in enumerate(rows):
            values.append({"group_id": symbol, "time_idx": index, **item})
        for index in range(FORECAST_HORIZON):
            values.append({
                "group_id": symbol,
                "time_idx": len(rows) + index,
                **{column: rows[-1][column] for column in FEATURE_COLUMNS},
            })
        frame = pd.DataFrame(values)
        self._load_model(frame)
        from pytorch_forecasting import TimeSeriesDataSet

        dataset = TimeSeriesDataSet.from_parameters(
            self._checkpoint["dataset_parameters"], frame, predict=True, stop_randomization=True
        )
        loader = dataset.to_dataloader(train=False, batch_size=1, num_workers=0)
        with torch.no_grad():
            quantiles = self.model.predict(loader, mode="quantiles").detach().cpu()[0]
        tft_attention = self._extract_tft_attention(loader)
        median = float(quantiles[-1, 3])
        lower = min(float(quantiles[-1, 1]), float(quantiles[-1, 5]))
        upper = max(float(quantiles[-1, 1]), float(quantiles[-1, 5]))
        median = min(max(median, lower), upper)
        result = {
            "symbol": symbol,
            "timestamp": features.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "current_price": round(current_price, 2),
            "predicted_price": round(median, 2),
            "lower_bound": round(max(0.01, lower), 2),
            "upper_bound": round(max(0.01, upper), 2),
            "direction": self._direction((median - current_price) / current_price),
            "confidence": round(max(0.0, min(0.99, 1 - abs(upper - lower) / max(current_price, 1))), 2),
        }
        if tft_attention is not None:
            result["tft_attention"] = tft_attention
        return result

    def _extract_tft_attention(self, loader: Any) -> dict[str, float] | None:
        """Return genuine TFT attention output when this library exposes it."""
        if self.model is None or not hasattr(self.model, "interpret_output"):
            return None
        try:
            raw = self.model.predict(loader, mode="raw")
            raw_output = getattr(raw, "output", raw)
            interpreted = self.model.interpret_output(raw_output)
            attention = interpreted.get("attention")
            if attention is None:
                return None
            values = attention.detach().cpu().flatten().tolist()
            return {f"step_{index + 1}": round(float(value), 6) for index, value in enumerate(values)}
        except (AttributeError, KeyError, TypeError, RuntimeError, ValueError):
            # A missing/incompatible interpretation is not a reason to invent weights.
            return None

    def _direction(self, signal: float) -> str:
        if abs(signal) <= self.neutral_threshold:
            return "NEUTRAL"
        if signal >= self.direction_threshold:
            return "UP"
        if signal <= -self.direction_threshold:
            return "DOWN"
        return "NEUTRAL"

    @staticmethod
    def _number(features: Dict[str, Any], key: str, default: float = 0.0) -> float:
        try:
            return float(features.get(key, default))
        except (TypeError, ValueError):
            return default

    def _sentiment_signal(self, features: Dict[str, Any]) -> float:
        if "normalized_score" in features:
            return max(-1.0, min(1.0, self._number(features, "normalized_score")))
        raw_score = self._number(features, "sentiment_score", features.get("score", 0.0))
        if raw_score < 0:
            return max(-1.0, raw_score)
        score = min(1.0, raw_score)
        label = str(features.get("sentiment", "neutral")).lower()
        return score if label == "positive" else -score if label == "negative" else 0.0

    def _momentum_signal(self, features: Dict[str, Any], current_price: float) -> float:
        momentum = self._number(features, "price_momentum", float("nan"))
        if momentum != momentum:
            momentum = self._number(features, "price_change_pct")
        elif abs(momentum) > 1:
            momentum /= current_price
        return max(-1.0, min(1.0, momentum / 0.02))

    def _liquidity_signal(self, features: Dict[str, Any]) -> float:
        score = self._number(features, "liquidity_score", 50.0)
        normalized = score / 100.0 if score > 1 else score
        return max(-1.0, min(1.0, 0.5 - normalized))

    @staticmethod
    def _risk_signal(sentiment: float, imbalance: float, momentum: float, liquidity: float, direction: str) -> str:
        negatives = sum((sentiment < -0.25, imbalance < -0.25, momentum < -0.10, liquidity > 0.15))
        if direction == "DOWN" and negatives >= 3:
            return "HIGH_RISK"
        if negatives >= 2 or (direction == "DOWN" and negatives):
            return "WATCH"
        return "NORMAL"
