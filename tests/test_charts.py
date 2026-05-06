from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pandas as pd

from backtester.engine import BacktestConfig
from backtester.engine.backtest import BacktestResult
from backtester.portfolio import Side, Trade
from backtester.viz import (
    plot_drawdown,
    plot_equity_curve,
    plot_strategy_comparison,
    plot_trades,
)


def make_result(strategy_name: str = "TestStrategy") -> BacktestResult:
    equity = pd.Series(
        [100.0, 105.0, 103.0],
        index=pd.date_range("2020-01-01", periods=3, name="date"),
        name="equity",
    )
    return BacktestResult(
        config=BacktestConfig("AAPL", "2020-01-01", "2020-01-03"),
        strategy_name=strategy_name,
        equity_curve=equity,
        trades=[],
        final_value=103.0,
        initial_value=100.0,
    )


def assert_png_written(path: Path) -> None:
    assert path.exists()
    assert path.stat().st_size > 0


def test_plot_equity_curve_saves_png(tmp_path: Path) -> None:
    path = tmp_path / "charts" / "equity.png"

    plot_equity_curve(make_result(), save_path=str(path))

    assert_png_written(path)


def test_plot_drawdown_saves_png_for_empty_curve(tmp_path: Path) -> None:
    path = tmp_path / "drawdown.png"

    plot_drawdown(pd.Series(dtype="float64"), save_path=str(path))

    assert_png_written(path)


def test_plot_trades_saves_png_with_and_without_trades(tmp_path: Path) -> None:
    price_data = pd.DataFrame(
        {"close": [100.0, 105.0, 103.0]},
        index=pd.date_range("2020-01-01", periods=3, name="date"),
    )
    trades = [
        Trade("AAPL", Side.BUY, 1, 100.0, 0.0, datetime(2020, 1, 1)),
        Trade("AAPL", Side.SELL, 1, 105.0, 0.0, datetime(2020, 1, 2)),
    ]
    path_with_trades = tmp_path / "trades.png"
    path_empty_trades = tmp_path / "trades_empty.png"

    plot_trades(price_data, trades, save_path=str(path_with_trades))
    plot_trades(price_data, [], save_path=str(path_empty_trades))

    assert_png_written(path_with_trades)
    assert_png_written(path_empty_trades)


def test_plot_strategy_comparison_saves_png_for_empty_results(tmp_path: Path) -> None:
    path_empty = tmp_path / "comparison_empty.png"
    path_results = tmp_path / "comparison_results.png"

    plot_strategy_comparison([], save_path=str(path_empty))
    plot_strategy_comparison([make_result("A"), make_result("B")], save_path=str(path_results))

    assert_png_written(path_empty)
    assert_png_written(path_results)

