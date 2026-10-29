"""Temporal Fusion Transformer configuration and checkpoint helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch

FORECAST_HORIZON = 5
FEATURE_COLUMNS = (
    "price",
    "spread",
    "order_book_imbalance",
    "total_bid_volume",
    "total_ask_volume",
    "price_change",
    "rolling_volatility",
    "liquidity_score",
    "sentiment_score",
)


def build_tft(dataset: Any, *, hidden_size: int = 16, attention_heads: int = 2,
              dropout: float = 0.1) -> Any:
    """Build a small quantile TFT from a :class:`TimeSeriesDataSet`."""
    from pytorch_forecasting import TemporalFusionTransformer
    from pytorch_forecasting.metrics import QuantileLoss

    return TemporalFusionTransformer.from_dataset(
        dataset,
        hidden_size=hidden_size,
        attention_head_size=attention_heads,
        dropout=dropout,
        hidden_continuous_size=hidden_size,
        output_size=7,
        loss=QuantileLoss(quantiles=[0.02, 0.1, 0.25, 0.5, 0.75, 0.9, 0.98]),
        log_interval=-1,
        reduce_on_plateau_patience=3,
    )


def save_checkpoint(path: str | Path, model: Any, dataset: Any,
                    *, hidden_size: int, attention_heads: int,
                    dropout: float) -> None:
    """Persist weights and dataset metadata, without serializing the trainer."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "dataset_parameters": dataset.get_parameters(),
            "model_config": {
                "hidden_size": hidden_size,
                "attention_heads": attention_heads,
                "dropout": dropout,
            },
        },
        target,
    )


def load_checkpoint(path: str | Path, dataset: Any,
                    map_location: str | torch.device = "cpu") -> tuple[Any, dict[str, Any]]:
    """Load a TFT checkpoint and return the model plus its metadata."""
    checkpoint = torch.load(path, map_location=map_location, weights_only=False)
    model = build_tft(dataset, **checkpoint["model_config"])
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model, checkpoint
