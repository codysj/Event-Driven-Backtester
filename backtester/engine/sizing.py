"""Position sizing helpers shared by single- and multi-asset engines."""

from __future__ import annotations

import math

import pandas as pd

from backtester.engine.config import BacktestConfig, MultiAssetBacktestConfig, PositionSizeMethod


EngineConfig = BacktestConfig | MultiAssetBacktestConfig


def calculate_buy_quantity(
    *,
    config: EngineConfig,
    price: float,
    available_cash: float,
    portfolio_value: float,
    data: pd.DataFrame,
    current_index: int,
) -> int:
    """Return BUY quantity for the configured sizing method.

    ``VOLATILITY_TARGET`` is a simplified daily-volatility allocation model:
    allocation = portfolio_value * risk_fraction / realized_daily_volatility,
    capped at available cash.
    """
    if price <= 0:
        return 0

    method = config.position_size_method
    if method is PositionSizeMethod.ALL_IN:
        return int(available_cash // price)
    if method is PositionSizeMethod.FIXED_DOLLAR:
        return int(config.position_size_value // price)
    if method is PositionSizeMethod.FIXED_QUANTITY:
        return int(config.position_size_value)
    if method is PositionSizeMethod.PERCENT_EQUITY:
        allocation = min(portfolio_value * config.position_size_value, available_cash)
        return int(allocation // price)
    if method is PositionSizeMethod.VOLATILITY_TARGET:
        daily_volatility = _realized_daily_volatility(data, current_index, config.volatility_window)
        if daily_volatility <= 0.0 or math.isnan(daily_volatility):
            return 0
        allocation = portfolio_value * config.position_size_value / daily_volatility
        allocation = min(allocation, available_cash)
        return int(allocation // price)
    return 0


def _realized_daily_volatility(data: pd.DataFrame, current_index: int, window: int) -> float:
    if current_index < window:
        return 0.0

    closes = data["close"].iloc[current_index - window : current_index + 1]
    returns = closes.pct_change().dropna()
    if len(returns) < window:
        return 0.0
    return float(returns.std())
