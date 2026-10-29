"""Tests for timestamp-based fusion without data leakage."""

import pandas as pd

from app.fusion.timestamp_fusion import TimestampFusionService


def _market_frame(timestamps):
    n = len(timestamps)
    price_changes = [0.0]
    rolling_vols = [0.0]
    if n > 1:
        price_changes.extend([0.2, -0.05, 0.15, 0.20][: n - 1])
        rolling_vols.extend([0.01, 0.012, 0.013, 0.014][: n - 1])

    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(timestamps),
            "symbol": "DEMO",
            "last_price": [100.0 + i * 0.2 for i in range(n)],
            "spread": [0.1 - i * 0.005 for i in range(n)],
            "total_bid_volume": [1200 + i * 50 for i in range(n)],
            "total_ask_volume": [1100 + i * 50 for i in range(n)],
            "order_book_imbalance": [0.04 for _ in range(n)],
            "price_change": price_changes[:n],
            "rolling_volatility": rolling_vols[:n],
            "liquidity_score": [74.0 + i * 0.5 for i in range(n)],
        }
    )


def test_future_news_is_not_visible_before_its_timestamp():
    service = TimestampFusionService()
    market = _market_frame([
        "2024-01-01 10:04:01",
        "2024-01-01 10:04:02",
        "2024-01-01 10:04:03",
        "2024-01-01 10:04:04",
        "2024-01-01 10:04:05",
    ])
    news = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-01-01 10:04:05"]),
            "symbol": ["DEMO"],
            "sentiment_score": [0.72],
            "news_id": ["news-0001"],
            "news_headline": ["Revenue beats expectations"],
        }
    )

    fused = service.perform_as_of_join(market, news)

    assert fused["sentiment_score"].iloc[:4].tolist() == [0.0, 0.0, 0.0, 0.0]
    assert fused["news_id"].iloc[:4].isna().all()
    assert fused["news_id"].iloc[4] == "news-0001"
    assert fused["sentiment_score"].iloc[4] == 0.72


def test_news_at_exact_market_timestamp_is_available():
    service = TimestampFusionService()
    market = _market_frame(["2024-01-01 10:04:05"])
    news = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2024-01-01 10:04:05"]),
            "symbol": ["DEMO"],
            "sentiment_score": [0.91],
            "news_id": ["news-eq"],
            "news_headline": ["Earnings meet guidance"],
        }
    )

    fused = service.perform_as_of_join(market, news)

    assert fused["news_id"].iloc[0] == "news-eq"
    assert fused["sentiment_score"].iloc[0] == 0.91
    assert fused["news_timestamp"].iloc[0] == pd.Timestamp("2024-01-01 10:04:05")


def test_multiple_news_items_select_latest_valid_one():
    service = TimestampFusionService()
    market = _market_frame([
        "2024-01-01 10:04:01",
        "2024-01-01 10:04:02",
        "2024-01-01 10:04:03",
    ])
    news = pd.DataFrame(
        {
            "timestamp": pd.to_datetime([
                "2024-01-01 10:04:01",
                "2024-01-01 10:04:02",
                "2024-01-01 10:04:04",
            ]),
            "symbol": ["DEMO", "DEMO", "DEMO"],
            "sentiment_score": [0.25, -0.5, 0.9],
            "news_id": ["news-old", "news-newer", "news-future"],
            "news_headline": ["Slight rebound", "Guidance cuts", "Future upgrade"],
        }
    )

    fused = service.perform_as_of_join(market, news)

    assert fused["news_id"].iloc[0] == "news-old"
    assert fused["news_id"].iloc[1] == "news-newer"
    assert fused["news_id"].iloc[2] == "news-newer"
    assert fused["sentiment_score"].iloc[2] == -0.5
