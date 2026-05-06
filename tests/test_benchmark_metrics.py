from __future__ import annotations

import pandas as pd
import pytest

from backtester.engine import BacktestConfig
from backtester.engine.backtest import BacktestResult
from backtester.metrics import (
    alpha_beta,
    buy_and_hold_equity,
    excess_returns,
    generate_report,
    information_ratio,
)


def test_buy_and_hold_equity_known_example() -> None:
    data = pd.DataFrame(
        {"close": [10.0, 12.0, 15.0]},
        index=pd.date_range("2020-01-01", periods=3, name="date"),
    )

    equity = buy_and_hold_equity(data, initial_cash=105.0)

    assert list(equity) == [105.0, 125.0, 155.0]
    assert equity.name == "benchmark_equity"


def test_excess_returns_aligns_common_index() -> None:
    strategy = pd.Series([100.0, 110.0, 121.0], index=pd.date_range("2020-01-01", periods=3))
    benchmark = pd.Series([100.0, 105.0, 110.25], index=pd.date_range("2020-01-02", periods=3))

    excess = excess_returns(strategy, benchmark)

    assert len(excess) == 1
    assert excess.name == "excess_returns"


def test_alpha_beta_known_linear_relation() -> None:
    benchmark = pd.Series([0.01, 0.02, -0.01, 0.03])
    strategy = 2 * benchmark

    alpha, beta = alpha_beta(strategy, benchmark)

    assert alpha == pytest.approx(0.0)
    assert beta == pytest.approx(2.0)


def test_alpha_beta_zero_variance_safe() -> None:
    alpha, beta = alpha_beta(pd.Series([0.01, 0.02]), pd.Series([0.0, 0.0]))

    assert (alpha, beta) == (0.0, 0.0)


def test_information_ratio_known_series() -> None:
    strategy = pd.Series([0.02, 0.01, 0.03])
    benchmark = pd.Series([0.01, 0.01, 0.01])
    active = strategy - benchmark
    expected = active.mean() / active.std() * (252**0.5)

    assert information_ratio(strategy, benchmark) == pytest.approx(expected)


def test_generate_report_adds_benchmark_keys_only_when_provided() -> None:
    equity = pd.Series([100.0, 110.0, 120.0], index=pd.date_range("2020-01-01", periods=3))
    benchmark = pd.Series([100.0, 105.0, 115.0], index=equity.index)
    result = BacktestResult(
        config=BacktestConfig("AAPL", "2020-01-01", "2020-01-03"),
        strategy_name="Test",
        equity_curve=equity,
        trades=[],
        final_value=120.0,
        initial_value=100.0,
    )

    base_report = generate_report(result)
    benchmark_report = generate_report(result, benchmark_equity=benchmark)

    assert "benchmark_total_return" not in base_report
    assert "benchmark_total_return" in benchmark_report
    assert "alpha" in benchmark_report
    assert "beta" in benchmark_report

