from __future__ import annotations

from datetime import datetime
import math

import pandas as pd
import pytest

from backtester.engine import BacktestConfig
from backtester.engine.backtest import BacktestResult
from backtester.metrics import (
    annualized_return,
    best_worst_day,
    conditional_value_at_risk,
    drawdown_duration_days,
    generate_report,
    max_drawdown,
    monthly_returns,
    profit_factor,
    rolling_drawdown,
    rolling_sharpe_ratio,
    rolling_volatility,
    sharpe_ratio,
    sortino_ratio,
    total_return,
    value_at_risk,
    win_rate,
)
from backtester.portfolio import Side, Trade


def trade(side: Side, quantity: int, price: float, commission: float = 0.0) -> Trade:
    return Trade(
        ticker="AAPL",
        side=side,
        quantity=quantity,
        price=price,
        commission=commission,
        timestamp=datetime(2020, 1, 1),
    )


def test_total_return() -> None:
    assert total_return(100.0, 125.0) == pytest.approx(0.25)


def test_total_return_invalid_initial_value() -> None:
    with pytest.raises(ValueError):
        total_return(0.0, 125.0)

    with pytest.raises(ValueError):
        total_return(-100.0, 125.0)


def test_annualized_return_constant_or_short_curve() -> None:
    assert annualized_return(pd.Series([100.0])) == 0.0
    assert annualized_return(pd.Series(dtype="float64")) == 0.0


def test_annualized_return_known_values() -> None:
    equity = pd.Series([100.0, 110.0, 121.0])
    expected = (1 + 0.21) ** (1 / (2 / 252)) - 1

    assert annualized_return(equity) == pytest.approx(expected)


def test_sharpe_ratio_known_series() -> None:
    returns = pd.Series([0.01, 0.02, -0.01, 0.015, -0.005])
    expected = returns.mean() / returns.std() * math.sqrt(252)

    assert sharpe_ratio(returns) == pytest.approx(expected, abs=1e-6)


def test_sharpe_ratio_zero_std_returns_zero() -> None:
    assert sharpe_ratio(pd.Series([0.01, 0.01, 0.01])) == 0.0
    assert sharpe_ratio(pd.Series(dtype="float64")) == 0.0


def test_sortino_ratio_known_series() -> None:
    returns = pd.Series([0.01, 0.02, -0.01, 0.015, -0.005])
    downside = returns[returns < 0]
    expected = returns.mean() / downside.std() * math.sqrt(252)

    assert sortino_ratio(returns) == pytest.approx(expected, abs=1e-6)


def test_sortino_ratio_no_downside_returns_zero() -> None:
    assert sortino_ratio(pd.Series([0.01, 0.02, 0.03])) == 0.0


def test_max_drawdown_known_curve() -> None:
    equity = pd.Series([100.0, 110.0, 105.0, 95.0, 100.0, 120.0, 90.0])

    assert max_drawdown(equity) == pytest.approx(-0.25)


def test_max_drawdown_empty_curve() -> None:
    assert max_drawdown(pd.Series(dtype="float64")) == 0.0


def test_richer_risk_analytics_are_hand_checkable() -> None:
    equity = pd.Series(
        [100.0, 110.0, 99.0, 105.0, 95.0],
        index=pd.date_range("2020-01-01", periods=5, name="date"),
    )
    returns = equity.pct_change().dropna()

    assert best_worst_day(returns) == pytest.approx((0.1, -0.1))
    assert drawdown_duration_days(equity) == 3
    assert rolling_volatility(returns, window=2).iloc[-1] > 0
    assert rolling_sharpe_ratio(returns, window=2).iloc[-1] != 0
    assert rolling_drawdown(equity, window=5).iloc[-1] == pytest.approx((95.0 - 110.0) / 110.0)
    assert value_at_risk(returns, confidence=0.75) == pytest.approx(returns.quantile(0.25))
    assert conditional_value_at_risk(returns, confidence=0.75) <= value_at_risk(returns, confidence=0.75)


def test_monthly_returns_table() -> None:
    equity = pd.Series(
        [100.0, 110.0, 121.0],
        index=pd.to_datetime(["2020-01-31", "2020-02-28", "2020-03-31"]),
    )

    table = monthly_returns(equity)

    assert list(table["year"]) == [2020, 2020]
    assert list(table["month"]) == [2, 3]
    assert list(table["return"]) == pytest.approx([0.1, 0.1])


def test_win_rate() -> None:
    trades = [
        trade(Side.BUY, 10, 100.0),
        trade(Side.SELL, 10, 110.0),
        trade(Side.BUY, 10, 100.0),
        trade(Side.SELL, 10, 90.0),
        trade(Side.BUY, 10, 100.0),
        trade(Side.SELL, 10, 101.0),
    ]

    assert win_rate(trades) == pytest.approx(2 / 3)


def test_win_rate_zero_or_unmatched_trades() -> None:
    assert win_rate([]) == 0.0
    assert win_rate([trade(Side.BUY, 10, 100.0)]) == 0.0


def test_profit_factor() -> None:
    trades = [
        trade(Side.BUY, 10, 100.0, commission=1.0),
        trade(Side.SELL, 10, 110.0, commission=1.0),
        trade(Side.BUY, 10, 100.0, commission=1.0),
        trade(Side.SELL, 10, 95.0, commission=1.0),
    ]

    assert profit_factor(trades) == pytest.approx(98.0 / 52.0)


def test_profit_factor_infinite_when_no_gross_loss() -> None:
    trades = [
        trade(Side.BUY, 10, 100.0),
        trade(Side.SELL, 10, 110.0),
    ]

    assert profit_factor(trades) == float("inf")
    assert profit_factor([]) == 0.0


def test_generate_report_keys() -> None:
    equity = pd.Series(
        [100.0, 110.0, 105.0],
        index=pd.date_range("2020-01-01", periods=3, name="date"),
        name="equity",
    )
    trades = [trade(Side.BUY, 1, 100.0), trade(Side.SELL, 1, 110.0)]
    result = BacktestResult(
        config=BacktestConfig("AAPL", "2020-01-01", "2020-01-03"),
        strategy_name="TestStrategy",
        equity_curve=equity,
        trades=trades,
        final_value=105.0,
        initial_value=100.0,
    )

    report = generate_report(result)

    assert set(report) == {
        "strategy",
        "initial_value",
        "final_value",
        "total_return",
        "annualized_return",
        "sharpe_ratio",
        "sortino_ratio",
        "max_drawdown",
        "win_rate",
        "profit_factor",
        "total_trades",
        "trade_summary",
    }
    assert report["strategy"] == "TestStrategy"
    assert report["total_trades"] == 2
