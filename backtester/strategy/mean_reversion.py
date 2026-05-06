"""Bollinger-band-style mean reversion strategy."""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray
import pandas as pd

from backtester.strategy.base import Signal, Strategy


class MeanReversionStrategy(Strategy):
    """Generate one signal from the latest price's deviation from its mean."""

    def __init__(self, window: int = 20, num_std: float = 2.0) -> None:
        if window <= 0:
            msg = "window must be positive."
            raise ValueError(msg)
        if num_std <= 0:
            msg = "num_std must be positive."
            raise ValueError(msg)

        self._window = window
        self._num_std = num_std
        self._close: NDArray[np.float64] | None = None
        self._rolling_mean: NDArray[np.float64] | None = None
        self._rolling_std: NDArray[np.float64] | None = None
        self._precomputed_length: int | None = None

    @property
    def name(self) -> str:
        return f"MeanReversion({self._window}, {self._num_std}{chr(963)})"

    def precompute(self, data: pd.DataFrame) -> None:
        close = data["close"]
        self._close = close.to_numpy(dtype=float)
        self._rolling_mean = close.rolling(self._window).mean().to_numpy(dtype=float)
        self._rolling_std = close.rolling(self._window).std().to_numpy(dtype=float)
        self._precomputed_length = len(data)

    def generate_signal(self, data: pd.DataFrame, current_index: int) -> Signal:
        if current_index < self._window - 1:
            return Signal.HOLD

        needs_precompute = (
            self._close is None
            or self._rolling_mean is None
            or self._rolling_std is None
            or self._precomputed_length != len(data)
        )
        if needs_precompute:
            self.precompute(data)

        if self._close is None or self._rolling_mean is None or self._rolling_std is None:
            return Signal.HOLD

        current_price = float(self._close[current_index])
        mean = float(self._rolling_mean[current_index])
        std = float(self._rolling_std[current_index])
        if math.isnan(mean) or math.isnan(std) or std == 0.0:
            return Signal.HOLD

        upper = mean + self._num_std * std
        lower = mean - self._num_std * std

        if current_price <= lower:
            return Signal.BUY
        if current_price >= upper:
            return Signal.SELL
        return Signal.HOLD
