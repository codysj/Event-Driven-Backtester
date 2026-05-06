"""Types and exceptions for the Backtester data layer."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BarData:
    """Single complete OHLCV bar."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class TickerNotFoundError(ValueError):
    """Raised when a ticker appears invalid or no usable ticker data exists."""


class NoDataError(ValueError):
    """Raised when a request cannot produce any OHLCV rows."""

