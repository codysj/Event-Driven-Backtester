from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pytest

from backtester.data.loader import DataLoader
from backtester.engine import BacktestConfig, BacktestEngine, PositionSizeMethod
from backtester.strategy import Signal, Strategy


def make_ohlcv_df(close_prices: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": close_prices,
            "high": close_prices,
            "low": close_prices,
            "close": close_prices,
            "volume": [100] * len(close_prices),
        },
        index=pd.date_range("2020-01-01", periods=len(close_prices), name="date"),
    )


@dataclass
class FakeLoader(DataLoader):
    data: pd.DataFrame

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        return self.data.copy()


class AlwaysHoldStrategy(Strategy):
    @property
    def name(self) -> str:
        return "AlwaysHold"

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        return Signal.HOLD


class BuyFirstBarStrategy(Strategy):
    @property
    def name(self) -> str:
        return "BuyFirstBar"

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        if len(data) == 1:
            return Signal.BUY
        return Signal.HOLD


class BuyThenSellStrategy(Strategy):
    @property
    def name(self) -> str:
        return "BuyThenSell"

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        if len(data) == 1:
            return Signal.BUY
        if len(data) == 2:
            return Signal.SELL
        return Signal.HOLD


class RecordingLengthStrategy(Strategy):
    def __init__(self) -> None:
        self.lengths: list[int] = []

    @property
    def name(self) -> str:
        return "RecordingLength"

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        self.lengths.append(len(data))
        return Signal.HOLD


def make_engine(
    data: pd.DataFrame,
    strategy: Strategy,
    config: BacktestConfig,
) -> BacktestEngine:
    return BacktestEngine(loader=FakeLoader(data), strategy=strategy, config=config)


def test_no_trade_strategy_equity_curve_flat() -> None:
    config = BacktestConfig("AAPL", "2020-01-01", "2020-01-04", initial_cash=1_000.0)
    result = make_engine(make_ohlcv_df([100.0, 105.0, 110.0]), AlwaysHoldStrategy(), config).run()

    assert len(result.equity_curve) == 3
    assert list(result.equity_curve) == [1_000.0, 1_000.0, 1_000.0]
    assert result.trades == []


def test_buy_and_hold_final_value_hand_calculation() -> None:
    config = BacktestConfig(
        "AAPL",
        "2020-01-01",
        "2020-01-04",
        initial_cash=1_000.0,
        commission_rate=0.001,
        slippage_bps=5.0,
        position_size_method=PositionSizeMethod.FIXED_QUANTITY,
        position_size_value=5.0,
    )

    result = make_engine(make_ohlcv_df([100.0, 110.0, 120.0]), BuyFirstBarStrategy(), config).run()

    expected_entry_price = 100.0 * 1.0005
    expected_cash = round(1_000.0 - (5 * expected_entry_price + 0.005), 2)
    expected_final_value = expected_cash + 5 * 120.0
    assert result.final_value == pytest.approx(expected_final_value)


def test_buy_then_sell_cash_only_after_sell() -> None:
    config = BacktestConfig(
        "AAPL",
        "2020-01-01",
        "2020-01-04",
        initial_cash=1_000.0,
        commission_rate=0.0,
        slippage_bps=0.0,
        position_size_method=PositionSizeMethod.FIXED_QUANTITY,
        position_size_value=5.0,
    )

    result = make_engine(make_ohlcv_df([100.0, 110.0, 120.0]), BuyThenSellStrategy(), config).run()

    assert len(result.trades) == 2
    assert result.trades[-1].side.value == "SELL"
    assert result.final_value == pytest.approx(1_050.0)
    assert result.equity_curve.iloc[-1] == pytest.approx(1_050.0)


def test_lookahead_prevention_records_incremental_lengths() -> None:
    strategy = RecordingLengthStrategy()
    config = BacktestConfig("AAPL", "2020-01-01", "2020-01-05")

    make_engine(make_ohlcv_df([1.0, 2.0, 3.0, 4.0]), strategy, config).run()

    assert strategy.lengths == [1, 2, 3, 4]


def test_equity_curve_length_matches_data_length() -> None:
    config = BacktestConfig("AAPL", "2020-01-01", "2020-01-05")

    result = make_engine(make_ohlcv_df([10.0, 11.0, 12.0, 13.0]), AlwaysHoldStrategy(), config).run()

    assert len(result.equity_curve) == 4


def test_fixed_quantity_position_sizing() -> None:
    config = BacktestConfig(
        "AAPL",
        "2020-01-01",
        "2020-01-03",
        position_size_method=PositionSizeMethod.FIXED_QUANTITY,
        position_size_value=7.0,
    )

    result = make_engine(make_ohlcv_df([100.0, 100.0]), BuyFirstBarStrategy(), config).run()

    assert result.trades[0].quantity == 7


def test_fixed_dollar_position_sizing() -> None:
    config = BacktestConfig(
        "AAPL",
        "2020-01-01",
        "2020-01-03",
        position_size_method=PositionSizeMethod.FIXED_DOLLAR,
        position_size_value=250.0,
    )

    result = make_engine(make_ohlcv_df([100.0, 100.0]), BuyFirstBarStrategy(), config).run()

    assert result.trades[0].quantity == 2


def test_all_in_position_sizing() -> None:
    config = BacktestConfig(
        "AAPL",
        "2020-01-01",
        "2020-01-03",
        initial_cash=1_000.0,
        commission_rate=0.0,
        slippage_bps=0.0,
        position_size_method=PositionSizeMethod.ALL_IN,
    )

    result = make_engine(make_ohlcv_df([100.0, 100.0]), BuyFirstBarStrategy(), config).run()

    assert result.trades[0].quantity == 10


def test_non_positive_price_buy_signal_does_not_create_trade() -> None:
    config = BacktestConfig(
        "AAPL",
        "2020-01-01",
        "2020-01-03",
        position_size_method=PositionSizeMethod.FIXED_QUANTITY,
        position_size_value=7.0,
    )

    result = make_engine(make_ohlcv_df([0.0, 100.0]), BuyFirstBarStrategy(), config).run()

    assert result.trades == []
