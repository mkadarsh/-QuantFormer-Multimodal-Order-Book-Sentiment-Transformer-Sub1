"""
Mock financial news generator
"""
import logging
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Union

from app.config import get_settings
from app.schemas.news import NewsItem

logger = logging.getLogger(__name__)
settings = get_settings()

POSITIVE_NEWS = [
    "Company reports record quarterly earnings",
    "Revenue exceeds analyst expectations",
    "Company announces major expansion",
    "Company receives major new contract",
]

NEUTRAL_NEWS = [
    "Company announces quarterly results",
    "Company schedules investor meeting",
    "Company announces new product launch",
]

NEGATIVE_NEWS = [
    "Company warns of weaker earnings",
    "Regulatory investigation announced",
    "Company reports unexpected losses",
    "CEO resigns unexpectedly",
    "Company cuts revenue guidance",
]


class NewsSimulator:
    """Generates simulated financial news."""

    def __init__(
        self,
        symbols: Optional[Union[str, Sequence[str]]] = None,
        source: str = "MarketWire",
        update_interval_seconds: Optional[int] = None,
    ):
        """Initialize the simulator."""
        self.symbols = self._normalize_symbols(symbols or getattr(settings, "NEWS_SYMBOLS", ["DEMO"]))
        self.source = source
        self.update_interval_seconds = (
            update_interval_seconds
            or getattr(settings, "NEWS_UPDATE_INTERVAL_SECONDS", None)
            or max(int(getattr(settings, "NEWS_UPDATE_INTERVAL_MS", 5000) / 1000), 1)
        )
        self.news_id_counter = 0

    @staticmethod
    def _normalize_symbols(symbols: Union[str, Sequence[str]]) -> List[str]:
        """Normalize the configured symbols into a list."""
        if isinstance(symbols, str):
            symbols = [symbol.strip() for symbol in symbols.split(",") if symbol.strip()]
        return [NewsItem(
            id=f"symbol-{index}",
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            headline="placeholder",
            source="init",
        ).symbol for index, symbol in enumerate(symbols)]

    def _pick_symbol(self) -> str:
        """Pick a symbol from the configured set."""
        return random.choice(self.symbols)

    def generate_news(self, symbol: Optional[str] = None) -> Dict:
        """Generate a random financial news item."""
        chosen_symbol = NewsItem(
            id="placeholder",
            timestamp=datetime.now(timezone.utc),
            symbol=symbol or self._pick_symbol(),
            headline="placeholder",
            source=self.source,
        ).symbol

        sentiment = random.choices(
            ["positive", "neutral", "negative"],
            weights=[0.4, 0.35, 0.25],
            k=1,
        )[0]

        if sentiment == "positive":
            headline = random.choice(POSITIVE_NEWS)
        elif sentiment == "negative":
            headline = random.choice(NEGATIVE_NEWS)
        else:
            headline = random.choice(NEUTRAL_NEWS)

        item = NewsItem(
            id=f"news-{self.news_id_counter:06d}",
            timestamp=datetime.now(timezone.utc),
            symbol=chosen_symbol,
            headline=headline,
            source=self.source,
        )
        self.news_id_counter += 1
        return item.model_dump(mode="json")

    def get_sentiment_type(self, headline: str) -> str:
        """Determine sentiment type from a headline."""
        normalized = headline.lower()
        positive_keywords = [
            "record", "exceeds", "expansion", "major new contract", "strong",
            "earnings", "expects", "growth", "launch", "meeting"
        ]
        negative_keywords = [
            "warns", "investigation", "losses", "resigns", "cuts", "weak", "regulatory"
        ]

        if any(keyword in normalized for keyword in positive_keywords):
            if any(keyword in normalized for keyword in negative_keywords):
                return "neutral"
            return "positive"
        if any(keyword in normalized for keyword in negative_keywords):
            return "negative"
        return "neutral"

    def stream_news(self, symbol: Optional[str] = None, interval_seconds: Optional[int] = None, max_messages: Optional[int] = None):
        """Yield news items at a fixed interval until interrupted."""
        interval = interval_seconds or self.update_interval_seconds
        sent = 0
        while max_messages is None or sent < max_messages:
            yield self.generate_news(symbol=symbol)
            sent += 1
            if max_messages is not None and sent >= max_messages:
                break
            time.sleep(interval)
