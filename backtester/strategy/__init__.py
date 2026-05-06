"""Strategy abstractions and built-in strategy implementations."""

from backtester.strategy.base import Signal, Strategy
from backtester.strategy.mean_reversion import MeanReversionStrategy
from backtester.strategy.momentum import MomentumStrategy

__all__ = ["MeanReversionStrategy", "MomentumStrategy", "Signal", "Strategy"]

