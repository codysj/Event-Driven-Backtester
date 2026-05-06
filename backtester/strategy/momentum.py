"""Moving-average crossover momentum strategy."""

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

    @property
    def name(self) -> str:
        return f"Momentum({self._fast_window}/{self._slow_window})"

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        close = data["close"]
        if len(close) < self._slow_window + 1:
            return Signal.HOLD

        fast_now = float(close.iloc[-self._fast_window :].mean())
        fast_prev = float(close.iloc[-self._fast_window - 1 : -1].mean())
        slow_now = float(close.iloc[-self._slow_window :].mean())
        slow_prev = float(close.iloc[-self._slow_window - 1 : -1].mean())

        if fast_prev <= slow_prev and fast_now > slow_now:
            return Signal.BUY
        if fast_prev >= slow_prev and fast_now < slow_now:
            return Signal.SELL
        return Signal.HOLD

