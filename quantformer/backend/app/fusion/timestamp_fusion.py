"""Timestamp-safe as-of fusion for market and sentiment data."""

import pandas as pd


class TimestampFusionService:
    """Align sentiment to market observations without future-data leakage."""

    def perform_as_of_join(
        self, market_df: pd.DataFrame, sentiment_df: pd.DataFrame
    ) -> pd.DataFrame:
        market = market_df.copy()
        news = sentiment_df.copy()
        market["timestamp"] = pd.to_datetime(market["timestamp"])
        news["timestamp"] = pd.to_datetime(news["timestamp"])
        market = market.sort_values("timestamp")
        news = news.sort_values("timestamp").rename(columns={"timestamp": "news_timestamp"})
        result = pd.merge_asof(
            market,
            news,
            left_on="timestamp",
            right_on="news_timestamp",
            by="symbol",
            direction="backward",
        )
        if "sentiment_score" not in result:
            result["sentiment_score"] = 0.0
        result["sentiment_score"] = result["sentiment_score"].fillna(0.0)
        return result


TimestampFusion = TimestampFusionService
