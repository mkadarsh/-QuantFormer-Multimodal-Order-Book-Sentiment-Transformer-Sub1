"""Train and evaluate the QuantFormer Temporal Fusion Transformer."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import torch
from pytorch_forecasting import TimeSeriesDataSet
from pytorch_forecasting.data import GroupNormalizer
from lightning.pytorch import Trainer
from lightning.pytorch.callbacks import EarlyStopping

from app.models.tft_model import (
    FEATURE_COLUMNS,
    FORECAST_HORIZON,
    build_tft,
    save_checkpoint,
)

logger = logging.getLogger(__name__)
REQUIRED_COLUMNS = {
    "timestamp", "symbol", "last_price", *FEATURE_COLUMNS[1:],
}
ENCODER_LENGTH = 12


def load_and_prepare_data(path: str | Path) -> pd.DataFrame:
    """Load, validate, sort and normalize the fused market/news data."""
    frame = pd.read_csv(path)
    missing = sorted(REQUIRED_COLUMNS.difference(frame.columns))
    if missing:
        raise ValueError(f"Fused dataset is missing required columns: {', '.join(missing)}")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="raise")
    frame = frame.sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    frame["price"] = pd.to_numeric(frame["last_price"], errors="raise")
    for column in FEATURE_COLUMNS[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    frame["group_id"] = frame["symbol"].astype(str)
    frame["time_idx"] = frame.groupby("group_id").cumcount()
    return frame[["timestamp", "group_id", "time_idx", *FEATURE_COLUMNS]]


def create_datasets(frame: pd.DataFrame, validation_fraction: float = 0.2) -> tuple[Any, Any]:
    """Create chronological train/validation TimeSeriesDataSet objects."""
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1")
    cutoff = int(frame["time_idx"].max()) - max(FORECAST_HORIZON, int(len(frame) * validation_fraction))
    if cutoff < ENCODER_LENGTH:
        raise ValueError(
            f"Need at least {ENCODER_LENGTH + FORECAST_HORIZON + 1} rows per symbol "
            f"for a chronological TFT split; received {len(frame)} rows"
        )
    training = frame[frame.time_idx <= cutoff].copy()
    validation = frame[frame.time_idx > cutoff - ENCODER_LENGTH].copy()
    training_dataset = TimeSeriesDataSet(
        training,
        time_idx="time_idx",
        target="price",
        group_ids=["group_id"],
        min_encoder_length=ENCODER_LENGTH,
        max_encoder_length=ENCODER_LENGTH,
        min_prediction_length=FORECAST_HORIZON,
        max_prediction_length=FORECAST_HORIZON,
        static_categoricals=[],
        time_varying_known_reals=["time_idx"],
        time_varying_unknown_reals=list(FEATURE_COLUMNS),
        target_normalizer=GroupNormalizer(groups=["group_id"]),
        add_relative_time_idx=True,
        add_target_scales=True,
        add_encoder_length=True,
    )
    validation_dataset = TimeSeriesDataSet.from_dataset(
        training_dataset, validation, predict=True, stop_randomization=True
    )
    return training_dataset, validation_dataset


def _metrics(model: Any, loader: Any, device: str) -> tuple[float, float]:
    model.to(device)
    model.eval()
    absolute_errors: list[float] = []
    squared_errors: list[float] = []
    with torch.no_grad():
        for batch in loader:
            x, y = batch
            x = {key: value.to(device) if hasattr(value, "to") else value for key, value in x.items()}
            prediction = model(x).prediction[..., 3].detach().cpu().numpy()
            actual = y[0].detach().cpu().numpy()
            error = prediction - actual
            absolute_errors.extend(np.abs(error).ravel())
            squared_errors.extend(np.square(error).ravel())
    return float(np.mean(absolute_errors)), float(np.sqrt(np.mean(squared_errors)))


def train_model(data_path: str, output_path: str, epochs: int = 10, batch_size: int = 8) -> dict[str, float]:
    """Train a CPU-friendly TFT and save its weights and dataset metadata."""
    frame = load_and_prepare_data(data_path)
    training_dataset, validation_dataset = create_datasets(frame)
    train_loader = training_dataset.to_dataloader(train=True, batch_size=batch_size, num_workers=0)
    validation_loader = validation_dataset.to_dataloader(train=False, batch_size=batch_size, num_workers=0)
    model = build_tft(training_dataset)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    trainer = Trainer(
        max_epochs=epochs,
        accelerator="gpu" if device == "cuda" else "cpu",
        devices=1,
        enable_progress_bar=False,
        enable_model_summary=False,
        logger=False,
        callbacks=[EarlyStopping(monitor="val_loss", patience=3, mode="min")],
    )
    logger.info("Training TFT on %s", device)
    trainer.fit(model, train_dataloaders=train_loader, val_dataloaders=validation_loader)
    mae, rmse = _metrics(model, validation_loader, device)
    logger.info("Validation MAE=%.6f RMSE=%.6f", mae, rmse)
    print(f"Validation MAE: {mae:.6f}")
    print(f"Validation RMSE: {rmse:.6f}")
    save_checkpoint(output_path, model, training_dataset, hidden_size=16, attention_heads=2, dropout=0.1)
    logger.info("Saved TFT model to %s", output_path)
    return {"mae": mae, "rmse": rmse}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    backend_dir = Path(__file__).resolve().parents[1]
    parser.add_argument("--data", default=str(backend_dir / "data" / "fused_market_news.csv"))
    parser.add_argument("--output", default=str(backend_dir / "models" / "tft_model.pt"))
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    train_model(args.data, args.output, args.epochs, args.batch_size)
