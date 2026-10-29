"""FinBERT financial-news sentiment processing."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

MODEL_NAME = "ProsusAI/finbert"
# FinBERT produces 768-dimensional hidden states.  A pooled, deterministic
# 128-dimensional representation keeps Kafka messages and historical storage
# manageable for the MVP.
EMBEDDING_DIMENSION = 128
LABELS = ("positive", "negative", "neutral")


class FinBERTSentimentService:
    """Load FinBERT once and classify financial headlines."""

    def __init__(
        self,
        device: Optional[str] = None,
        model_name: str = MODEL_NAME,
        embedding_dimension: int = EMBEDDING_DIMENSION,
    ) -> None:
        self.model_name = model_name
        self.embedding_dimension = embedding_dimension
        self.device = self._select_device(device)
        self.model: Any = None
        self.tokenizer: Any = None
        self._torch: Any = None
        self._load_model()

    @staticmethod
    def _select_device(requested: Optional[str]) -> str:
        try:
            import torch
        except ImportError:
            if requested and requested != "cpu":
                raise RuntimeError("PyTorch is required for FinBERT inference")
            return "cpu"
        if requested:
            if requested.startswith("cuda") and not torch.cuda.is_available():
                logger.warning("CUDA requested but unavailable; using CPU")
                return "cpu"
            return requested
        return "cuda" if torch.cuda.is_available() else "cpu"

    def _load_model(self) -> None:
        """Download and initialize tokenizer/model exactly once per service."""
        logger.info("Loading FinBERT model %s on %s", self.model_name, self.device)
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            self._torch = torch
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name
            )
            self.model.to(self.device)
            self.model.eval()
            logger.info("FinBERT model loaded successfully on %s", self.device)
        except Exception as exc:
            self.model = None
            self.tokenizer = None
            logger.exception("Failed to load FinBERT model: %s", exc)

    @staticmethod
    def normalize_score(sentiment: str, score: float) -> float:
        """Return a signed confidence score in the range [-1, 1]."""
        if sentiment not in LABELS:
            raise ValueError(f"Unknown sentiment label: {sentiment}")
        confidence = max(0.0, min(1.0, float(score)))
        if sentiment == "positive":
            return confidence
        if sentiment == "negative":
            return -confidence
        return 0.0

    def analyze(self, text: str) -> Dict[str, Any]:
        """Classify one headline and return sentiment, confidence, and embedding."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("headline must be a non-empty string")
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("FinBERT model is unavailable")

        try:
            encoded = self.tokenizer(
                text.strip(),
                return_tensors="pt",
                truncation=True,
                max_length=512,
            )
            encoded = {key: value.to(self.device) for key, value in encoded.items()}
            with self._torch.no_grad():
                result = self.model(**encoded, output_hidden_states=True)
            probabilities = self._torch.softmax(result.logits, dim=-1)[0]
            class_index = int(self._torch.argmax(probabilities).item())
            label = self._label_for_index(class_index)
            confidence = float(probabilities[class_index].item())
            embedding = self._extract_embedding(result, encoded["attention_mask"])
            return {
                "sentiment": label,
                "score": confidence,
                "normalized_score": self.normalize_score(label, confidence),
                "embedding": embedding,
            }
        except ValueError:
            raise
        except Exception as exc:
            logger.exception("FinBERT inference failed for headline: %s", exc)
            raise RuntimeError("FinBERT inference failed") from exc

    def process_news(self, news: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enrich a news event for the sentiment-data topic."""
        if not isinstance(news, dict):
            raise ValueError("news event must be an object")
        news_id = news.get("news_id", news.get("id"))
        headline = news.get("headline")
        if not news_id or not isinstance(headline, str) or not headline.strip():
            raise ValueError("news event requires news_id/id and a non-empty headline")
        result = self.analyze(headline)
        return {
            "news_id": str(news_id),
            "symbol": str(news.get("symbol", "DEMO")),
            "timestamp": news.get("timestamp"),
            "headline": headline.strip(),
            **result,
        }

    def _label_for_index(self, index: int) -> str:
        id2label = getattr(getattr(self.model, "config", None), "id2label", {})
        label = str(id2label.get(index, id2label.get(str(index), ""))).lower()
        if label in LABELS:
            return label
        # FinBERT's published class order is positive, negative, neutral.
        if 0 <= index < len(LABELS):
            return LABELS[index]
        raise RuntimeError(f"FinBERT returned unsupported class index: {index}")

    def _extract_embedding(self, result: Any, attention_mask: Any) -> list[float]:
        hidden_states = getattr(result, "hidden_states", None)
        if not hidden_states:
            raise RuntimeError("FinBERT did not return hidden states")
        hidden = hidden_states[-1]
        mask = attention_mask.unsqueeze(-1).to(hidden.dtype)
        pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        vector = pooled[0]
        if vector.shape[0] >= self.embedding_dimension:
            vector = vector[: self.embedding_dimension]
        else:
            vector = self._torch.nn.functional.pad(
                vector, (0, self.embedding_dimension - vector.shape[0])
            )
        return [float(value) for value in vector.detach().cpu().tolist()]


# Backwards-compatible name used by the Phase 4 scaffold.
SentimentAnalyzer = FinBERTSentimentService
