"""Backtest engine composition layer."""

from backtester.engine.backtest import BacktestEngine, BacktestResult
from backtester.engine.config import BacktestConfig, MultiAssetBacktestConfig, PositionSizeMethod
from backtester.engine.multi_asset import MultiAssetBacktestEngine, MultiAssetBacktestResult

__all__ = [
    "BacktestConfig",
    "BacktestEngine",
    "BacktestResult",
    "MultiAssetBacktestConfig",
    "MultiAssetBacktestEngine",
    "MultiAssetBacktestResult",
    "PositionSizeMethod",
]
