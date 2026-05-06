from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from backtester.data.loader import DataLoader
from backtester.engine import BacktestConfig, BacktestEngine, PositionSizeMethod
from backtester.strategy import Signal, Strategy


def make_ohlcv(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "volume": [100] * len(closes),
        },
        index=pd.date_range("2020-01-01", periods=len(closes), name="date"),
    )


@dataclass
class FakeLoader(DataLoader):
    data: pd.DataFrame

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        del ticker, start, end
        return self.data.copy()


class BuyOnIndexStrategy(Strategy):
    def __init__(self, buy_index: int) -> None:
        self._buy_index = buy_index

    @property
    def name(self) -> str:
        return "BuyOnIndex"

    def generate_signal(self, data: pd.DataFrame, current_index: int) -> Signal:
        del data
        return Signal.BUY if current_index == self._buy_index else Signal.HOLD


def run_with_config(config: BacktestConfig, closes: list[float], buy_index: int) -> int:
    result = BacktestEngine(FakeLoader(make_ohlcv(closes)), BuyOnIndexStrategy(buy_index), config).run()
    return result.trades[0].quantity if result.trades else 0


def test_percent_equity_position_sizing() -> None:
    config = BacktestConfig(
        ticker="AAPL",
        start_date="2020-01-01",
        end_date="2020-01-03",
        initial_cash=100_000.0,
        commission_rate=0.0,
        slippage_bps=0.0,
        position_size_method=PositionSizeMethod.PERCENT_EQUITY,
        position_size_value=0.10,
    )

    assert run_with_config(config, [100.0, 100.0], buy_index=0) == 100


def test_percent_equity_caps_to_available_cash() -> None:
    config = BacktestConfig(
        ticker="AAPL",
        start_date="2020-01-01",
        end_date="2020-01-03",
        initial_cash=1_000.0,
        commission_rate=0.0,
        slippage_bps=0.0,
        position_size_method=PositionSizeMethod.PERCENT_EQUITY,
        position_size_value=1.0,
    )

    assert run_with_config(config, [100.0, 100.0], buy_index=0) == 10


def test_volatility_target_returns_zero_with_insufficient_history() -> None:
    config = BacktestConfig(
        ticker="AAPL",
        start_date="2020-01-01",
        end_date="2020-01-03",
        position_size_method=PositionSizeMethod.VOLATILITY_TARGET,
        position_size_value=0.01,
        volatility_window=3,
    )

    assert run_with_config(config, [100.0, 101.0, 102.0], buy_index=1) == 0


def test_volatility_target_returns_zero_when_volatility_is_zero() -> None:
    config = BacktestConfig(
        ticker="AAPL",
        start_date="2020-01-01",
        end_date="2020-01-05",
        position_size_method=PositionSizeMethod.VOLATILITY_TARGET,
        position_size_value=0.01,
        volatility_window=2,
    )

    assert run_with_config(config, [100.0, 100.0, 100.0, 100.0], buy_index=2) == 0


def test_volatility_target_produces_positive_quantity() -> None:
    config = BacktestConfig(
        ticker="AAPL",
        start_date="2020-01-01",
        end_date="2020-01-05",
        initial_cash=100_000.0,
        commission_rate=0.0,
        slippage_bps=0.0,
        position_size_method=PositionSizeMethod.VOLATILITY_TARGET,
        position_size_value=0.01,
        volatility_window=2,
    )

    assert run_with_config(config, [100.0, 110.0, 100.0, 105.0], buy_index=2) > 0
