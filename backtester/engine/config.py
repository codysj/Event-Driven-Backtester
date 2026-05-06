"""Configuration for backtest execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PositionSizeMethod(Enum):
    """Available methods for translating BUY signals into order quantities."""

    FIXED_QUANTITY = "FIXED_QUANTITY"
    FIXED_DOLLAR = "FIXED_DOLLAR"
    ALL_IN = "ALL_IN"


@dataclass(frozen=True)
class BacktestConfig:
    """Immutable configuration for a single backtest run."""

    ticker: str
    start_date: str
    end_date: str
    initial_cash: float = 100_000.0
    commission_rate: float = 0.001
    slippage_bps: float = 5.0
    position_size_method: PositionSizeMethod = PositionSizeMethod.FIXED_DOLLAR
    position_size_value: float = 10_000.0

    def __post_init__(self) -> None:
        if not self.ticker.strip():
            msg = "ticker must be non-empty."
            raise ValueError(msg)
        if self.initial_cash <= 0:
            msg = "initial_cash must be positive."
            raise ValueError(msg)
        if self.commission_rate < 0:
            msg = "commission_rate must be non-negative."
            raise ValueError(msg)
        if self.slippage_bps < 0:
            msg = "slippage_bps must be non-negative."
            raise ValueError(msg)
        if self.position_size_value <= 0:
            msg = "position_size_value must be positive."
            raise ValueError(msg)

