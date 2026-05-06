from __future__ import annotations

from datetime import datetime

import pandas as pd
import pytest

from backtester.portfolio import Order, Portfolio, Side


TIMESTAMP = datetime(2020, 1, 1)


def test_buy_reduces_cash_with_commission_and_slippage() -> None:
    portfolio = Portfolio(initial_cash=10_000.0, commission_rate=0.001)
    order = Order("AAPL", Side.BUY, 10, TIMESTAMP)

    trade = portfolio.execute_order(order, fill_price=100.0, slippage_bps=5.0)

    assert trade is not None
    assert trade.price == pytest.approx(100.05)
    assert portfolio.cash == pytest.approx(8_999.49)


def test_buy_creates_position_with_post_slippage_price() -> None:
    portfolio = Portfolio(initial_cash=10_000.0)
    order = Order("AAPL", Side.BUY, 10, TIMESTAMP)

    portfolio.execute_order(order, fill_price=100.0, slippage_bps=5.0)

    position = portfolio.get_position("AAPL")
    assert position is not None
    assert position.quantity == 10
    assert position.avg_entry_price == pytest.approx(100.05)


def test_sell_increases_cash_correctly() -> None:
    portfolio = Portfolio(initial_cash=10_000.0, commission_rate=0.001)
    portfolio.execute_order(Order("AAPL", Side.BUY, 10, TIMESTAMP), 100.0, slippage_bps=0.0)

    trade = portfolio.execute_order(Order("AAPL", Side.SELL, 4, TIMESTAMP), 110.0, slippage_bps=0.0)

    assert trade is not None
    assert portfolio.cash == pytest.approx(9_439.99)


def test_sell_removes_position_when_quantity_reaches_zero() -> None:
    portfolio = Portfolio(initial_cash=10_000.0)
    portfolio.execute_order(Order("AAPL", Side.BUY, 10, TIMESTAMP), 100.0, slippage_bps=0.0)

    portfolio.execute_order(Order("AAPL", Side.SELL, 10, TIMESTAMP), 100.0, slippage_bps=0.0)

    assert portfolio.get_position("AAPL") is None


def test_average_entry_price_updates_on_second_buy() -> None:
    portfolio = Portfolio(initial_cash=20_000.0, commission_rate=0.0)
    portfolio.execute_order(Order("AAPL", Side.BUY, 100, TIMESTAMP), 50.0, slippage_bps=0.0)
    portfolio.execute_order(Order("AAPL", Side.BUY, 50, TIMESTAMP), 60.0, slippage_bps=0.0)

    position = portfolio.get_position("AAPL")
    assert position is not None
    assert position.quantity == 150
    assert position.avg_entry_price == pytest.approx(53.3333333333)


def test_buy_rejected_when_insufficient_funds_without_mutation() -> None:
    portfolio = Portfolio(initial_cash=100.0)

    trade = portfolio.execute_order(Order("AAPL", Side.BUY, 2, TIMESTAMP), 100.0, slippage_bps=0.0)

    assert trade is None
    assert portfolio.cash == pytest.approx(100.0)
    assert portfolio.get_position("AAPL") is None
    assert portfolio.trade_history == []


def test_sell_rejected_when_no_position_exists() -> None:
    portfolio = Portfolio(initial_cash=1_000.0)

    trade = portfolio.execute_order(Order("AAPL", Side.SELL, 1, TIMESTAMP), 100.0)

    assert trade is None
    assert portfolio.cash == pytest.approx(1_000.0)
    assert portfolio.trade_history == []


def test_sell_rejected_when_quantity_exceeds_position() -> None:
    portfolio = Portfolio(initial_cash=1_000.0)
    portfolio.execute_order(Order("AAPL", Side.BUY, 5, TIMESTAMP), 100.0, slippage_bps=0.0)
    cash_after_buy = portfolio.cash

    trade = portfolio.execute_order(Order("AAPL", Side.SELL, 6, TIMESTAMP), 100.0)

    assert trade is None
    assert portfolio.cash == cash_after_buy
    assert len(portfolio.trade_history) == 1


def test_buy_then_immediate_sell_loses_cash_to_commission_and_slippage() -> None:
    portfolio = Portfolio(initial_cash=10_000.0, commission_rate=0.001)
    portfolio.execute_order(Order("AAPL", Side.BUY, 10, TIMESTAMP), 100.0, slippage_bps=5.0)
    portfolio.execute_order(Order("AAPL", Side.SELL, 10, TIMESTAMP), 100.0, slippage_bps=5.0)

    assert portfolio.cash < 10_000.0


def test_equity_curve_length_after_multiple_records() -> None:
    portfolio = Portfolio(initial_cash=1_000.0)

    portfolio.record_equity(datetime(2020, 1, 1), {})
    portfolio.record_equity(datetime(2020, 1, 2), {})

    equity_curve = portfolio.get_equity_curve()
    assert len(equity_curve) == 2
    assert list(equity_curve) == [1_000.0, 1_000.0]


def test_total_value_sums_cash_and_market_value() -> None:
    portfolio = Portfolio(initial_cash=1_000.0, commission_rate=0.0)
    portfolio.execute_order(Order("AAPL", Side.BUY, 5, TIMESTAMP), 100.0, slippage_bps=0.0)

    assert portfolio.total_value({"AAPL": 120.0}) == pytest.approx(1_100.0)


def test_total_value_raises_for_missing_current_price() -> None:
    portfolio = Portfolio(initial_cash=1_000.0, commission_rate=0.0)
    portfolio.execute_order(Order("AAPL", Side.BUY, 5, TIMESTAMP), 100.0, slippage_bps=0.0)

    with pytest.raises(KeyError):
        portfolio.total_value({})


def test_trade_history_returns_defensive_copy() -> None:
    portfolio = Portfolio(initial_cash=1_000.0)
    portfolio.execute_order(Order("AAPL", Side.BUY, 1, TIMESTAMP), 100.0, slippage_bps=0.0)

    history = portfolio.trade_history
    history.clear()

    assert len(portfolio.trade_history) == 1


def test_get_equity_curve_works_when_empty() -> None:
    equity_curve = Portfolio(initial_cash=1_000.0).get_equity_curve()

    assert isinstance(equity_curve.index, pd.DatetimeIndex)
    assert equity_curve.name == "equity"
    assert equity_curve.empty

