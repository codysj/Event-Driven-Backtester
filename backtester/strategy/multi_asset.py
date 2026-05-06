"""Helpers for applying single-asset strategies across multiple tickers."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from backtester.strategy.base import MultiAssetStrategy, Signal, Strategy


class SingleStrategyMultiAssetWrapper(MultiAssetStrategy):
    """Apply one Strategy factory independently to every ticker.

    A fresh Strategy instance is created per ticker during ``precompute`` so
    cached indicators cannot leak across assets.
    """

    def __init__(self, strategy_factory: Callable[[], Strategy]) -> None:
        self._strategy_factory = strategy_factory
        self._strategies: dict[str, Strategy] = {}

    @property
    def name(self) -> str:
        sample_strategy = self._strategy_factory()
        return f"MultiAsset({sample_strategy.name})"

    def precompute(self, data: dict[str, pd.DataFrame]) -> None:
        self._strategies = {}
        for ticker, frame in data.items():
            strategy = self._strategy_factory()
            strategy.precompute(frame)
            self._strategies[ticker] = strategy

    def generate_signals(
        self,
        data: dict[str, pd.DataFrame],
        current_index: int,
    ) -> dict[str, Signal]:
        if set(self._strategies) != set(data):
            self.precompute(data)

        return {
            ticker: self._strategies[ticker].generate_signal(frame, current_index)
            for ticker, frame in data.items()
        }
