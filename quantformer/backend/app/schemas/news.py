"""
Pydantic schemas for news data
"""
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NewsItem(BaseModel):
    """Individual news item."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(..., min_length=1)
    timestamp: datetime
    symbol: str = Field(..., min_length=1, max_length=10)
    headline: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, value: str) -> str:
        """Validate that symbols are uppercase ticker-like strings."""
        value = value.strip().upper()
        if not re.fullmatch(r"^[A-Z0-9._-]{1,10}$", value):
            raise ValueError(
                "symbol must be 1-10 characters and contain only letters, numbers, ., _, or -"
            )
        return value

    @field_validator("headline")
    @classmethod
    def validate_headline(cls, value: str) -> str:
        """Ensure headlines are non-empty after trimming whitespace."""
        value = value.strip()
        if not value:
            raise ValueError("headline must not be empty")
        return value

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        """Ensure source remains populated."""
        value = value.strip()
        if not value:
            raise ValueError("source must not be empty")
        return value


class NewsDataRequest(BaseModel):
    """News data request."""

    symbol: str
    limit: int = 10
