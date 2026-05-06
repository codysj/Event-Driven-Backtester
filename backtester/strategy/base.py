"""Base interfaces for bar-by-bar trading strategies."""

from abc import ABC, abstractmethod
from enum import Enum

import pandas as pd


class Signal(Enum):
    """Trading action emitted for the current bar."""

    BUY = 1
    SELL = -1
    HOLD = 0


class Strategy(ABC):
    """Abstract interface for one-bar-at-a-time strategy decisions.

    ``generate_signal`` receives historical OHLCV data from the first available
    bar through the current bar. The final row is "now", so implementations
    should only use information available at that point in time. This singular
    bar-by-bar interface helps prevent look-ahead bias by avoiding full-series
    signal generation inside strategies.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable strategy name."""
        ...

    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """Return exactly one signal for the current bar."""
        ...
