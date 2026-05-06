"""Bollinger-band-style mean reversion strategy."""

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

    @property
    def name(self) -> str:
        return f"MeanReversion({self._window}, {self._num_std}σ)"

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        close = data["close"]
        if len(close) < self._window:
            return Signal.HOLD

        latest_window = close.iloc[-self._window :]
        mean = float(latest_window.mean())
        std = float(latest_window.std())
        if std == 0.0:
            return Signal.HOLD

        current_price = float(close.iloc[-1])
        upper = mean + self._num_std * std
        lower = mean - self._num_std * std

        if current_price <= lower:
            return Signal.BUY
        if current_price >= upper:
            return Signal.SELL
        return Signal.HOLD

