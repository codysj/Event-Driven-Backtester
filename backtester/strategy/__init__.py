"""Strategy abstractions and built-in strategy implementations."""

from backtester.strategy.base import MultiAssetStrategy, Signal, Strategy
from backtester.strategy.mean_reversion import MeanReversionStrategy
from backtester.strategy.momentum import MomentumStrategy
from backtester.strategy.multi_asset import SingleStrategyMultiAssetWrapper

__all__ = [
    "MeanReversionStrategy",
    "MomentumStrategy",
    "MultiAssetStrategy",
    "Signal",
    "SingleStrategyMultiAssetWrapper",
    "Strategy",
]

