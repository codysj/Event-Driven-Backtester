"""Moving-average crossover momentum strategy."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray
import pandas as pd

from backtester.strategy.base import Signal, Strategy


class MomentumStrategy(Strategy):
    """Generate one signal when fast and slow moving averages cross."""

    def __init__(self, fast_window: int = 10, slow_window: int = 50) -> None:
        if fast_window <= 0:
            msg = "fast_window must be positive."
            raise ValueError(msg)
        if slow_window <= 0:
            msg = "slow_window must be positive."
            raise ValueError(msg)
        if fast_window >= slow_window:
            msg = "fast_window must be less than slow_window."
            raise ValueError(msg)

        self._fast_window = fast_window
        self._slow_window = slow_window
        self._fast_sma: NDArray[np.float64] | None = None
        self._slow_sma: NDArray[np.float64] | None = None
        self._precomputed_length: int | None = None

    @property
    def name(self) -> str:
        return f"Momentum({self._fast_window}/{self._slow_window})"

    def precompute(self, data: pd.DataFrame) -> None:
        close = data["close"]
        self._fast_sma = close.rolling(self._fast_window).mean().to_numpy(dtype=float)
        self._slow_sma = close.rolling(self._slow_window).mean().to_numpy(dtype=float)
        self._precomputed_length = len(data)

    def generate_signal(self, data: pd.DataFrame, current_index: int) -> Signal:
        if current_index < self._slow_window:
            return Signal.HOLD

        if self._fast_sma is None or self._slow_sma is None or self._precomputed_length != len(data):
            self.precompute(data)

        if self._fast_sma is None or self._slow_sma is None:
            return Signal.HOLD

        fast_now = float(self._fast_sma[current_index])
        fast_prev = float(self._fast_sma[current_index - 1])
        slow_now = float(self._slow_sma[current_index])
        slow_prev = float(self._slow_sma[current_index - 1])
        if any(math.isnan(value) for value in [fast_now, fast_prev, slow_now, slow_prev]):
            return Signal.HOLD

        if fast_prev <= slow_prev and fast_now > slow_now:
            return Signal.BUY
        if fast_prev >= slow_prev and fast_now < slow_now:
            return Signal.SELL
        return Signal.HOLD

