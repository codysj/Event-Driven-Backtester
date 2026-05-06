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

    Stage 7 optimizes the earlier sliced-DataFrame interface. ``data`` is now
    the full OHLCV DataFrame and ``current_index`` marks the current bar.
    Strategy implementations must not inspect rows after ``current_index``.
    This removes per-bar DataFrame copies, but shifts look-ahead prevention
    from structural enforcement to a documented strategy contract.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable strategy name."""
        ...

    def precompute(self, data: pd.DataFrame) -> None:
        """Precompute any indicators needed during the hot backtest loop."""

    @abstractmethod
    def generate_signal(self, data: pd.DataFrame, current_index: int) -> Signal:
        """Return exactly one signal for ``current_index``.

        ``data`` is the full DataFrame for performance. Implementations must
        only use values at indices ``<= current_index`` to avoid look-ahead
        bias.
        """
        ...
