from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from backtester.data.loader import DataLoader
from backtester.engine import BacktestConfig
from backtester.research import run_grid_search
from backtester.strategy import MomentumStrategy


@dataclass
class FakeLoader(DataLoader):
    data: pd.DataFrame

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        del ticker, start, end
        return self.data.copy()


def make_data() -> pd.DataFrame:
    closes = [100.0 + index for index in range(80)]
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


def test_grid_search_expands_and_returns_expected_columns() -> None:
    results = run_grid_search(
        loader=FakeLoader(make_data()),
        strategy_factory=MomentumStrategy,
        param_grid={"fast_window": [2, 3], "slow_window": [5, 6]},
        config=BacktestConfig("AAPL", "2020-01-01", "2020-03-01"),
    )

    assert len(results) == 4
    for column in ["fast_window", "slow_window", "final_value", "total_return", "sharpe_ratio", "max_drawdown", "total_trades", "error"]:
        assert column in results.columns


def test_grid_search_records_invalid_combo_error() -> None:
    results = run_grid_search(
        loader=FakeLoader(make_data()),
        strategy_factory=MomentumStrategy,
        param_grid={"fast_window": [5], "slow_window": [3]},
        config=BacktestConfig("AAPL", "2020-01-01", "2020-03-01"),
    )

    assert len(results) == 1
    assert results.loc[0, "error"]


def test_grid_search_sort_by_total_return() -> None:
    results = run_grid_search(
        loader=FakeLoader(make_data()),
        strategy_factory=MomentumStrategy,
        param_grid={"fast_window": [2, 3], "slow_window": [5]},
        config=BacktestConfig("AAPL", "2020-01-01", "2020-03-01"),
        sort_by="total_return",
        ascending=True,
    )

    assert list(results["total_return"]) == sorted(results["total_return"])

