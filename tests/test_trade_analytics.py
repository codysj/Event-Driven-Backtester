from __future__ import annotations

from datetime import datetime

import pytest

from backtester.metrics import pair_trades, trade_summary
from backtester.portfolio import Side, Trade


def trade(side: Side, price: float, day: int, quantity: int = 10, commission: float = 0.0) -> Trade:
    return Trade("AAPL", side, quantity, price, commission, datetime(2020, 1, day))


def test_pair_trades_known_round_trips_and_unmatched_ignored() -> None:
    trades = [
        trade(Side.BUY, 100.0, 1),
        trade(Side.SELL, 110.0, 4),
        trade(Side.BUY, 100.0, 5),
    ]

    pairs = pair_trades(trades)

    assert len(pairs) == 1
    assert pairs[0].pnl == pytest.approx(100.0)
    assert pairs[0].return_pct == pytest.approx(0.10)
    assert pairs[0].holding_period_days == 3


def test_trade_summary_three_pairs() -> None:
    trades = [
        trade(Side.BUY, 100.0, 1),
        trade(Side.SELL, 110.0, 2),
        trade(Side.BUY, 100.0, 3),
        trade(Side.SELL, 90.0, 4),
        trade(Side.BUY, 100.0, 5),
        trade(Side.SELL, 105.0, 7),
    ]

    summary = trade_summary(trades)

    assert summary["total_round_trips"] == 3
    assert summary["winning_trades"] == 2
    assert summary["losing_trades"] == 1
    assert summary["win_rate"] == pytest.approx(2 / 3)
    assert summary["avg_win"] == pytest.approx(75.0)
    assert summary["avg_loss"] == pytest.approx(-100.0)
    assert summary["max_win"] == pytest.approx(100.0)
    assert summary["max_loss"] == pytest.approx(-100.0)
    assert summary["avg_holding_period_days"] == pytest.approx(4 / 3)
    assert summary["best_trade_pnl"] == pytest.approx(100.0)
    assert summary["worst_trade_pnl"] == pytest.approx(-100.0)


def test_trade_summary_empty_safe() -> None:
    summary = trade_summary([])

    assert summary["total_round_trips"] == 0
    assert summary["avg_trade_pnl"] == 0.0

