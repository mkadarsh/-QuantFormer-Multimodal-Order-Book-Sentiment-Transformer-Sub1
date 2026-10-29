# Models Directory

This directory stores trained models and model artifacts:

## Files

- `tft_model.pt` – Trained Temporal Fusion Transformer model (Phase 10)
- `scaler.pkl` – Feature scaler for preprocessing (Phase 10)
- `transformers_cache/` – HuggingFace FinBERT model cache

## Model Training

To train the model, run:

```bash
python scripts/train_model.py \
  --market_data data/market_data.csv \
  --news_data data/news_data.csv \
  --output models/tft_model.pt
```

**Note**: Large model files are excluded from Git (see .gitignore).
