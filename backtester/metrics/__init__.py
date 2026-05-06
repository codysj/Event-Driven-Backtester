"""Performance metrics for completed backtests."""

from backtester.metrics.performance import (
    alpha_beta,
    annualized_return,
    buy_and_hold_equity,
    excess_returns,
    generate_report,
    information_ratio,
    max_drawdown,
    print_report,
    profit_factor,
    sharpe_ratio,
    sortino_ratio,
    total_return,
    win_rate,
)
from backtester.metrics.trades import TradePair, pair_trades, trade_summary

__all__ = [
    "TradePair",
    "alpha_beta",
    "annualized_return",
    "buy_and_hold_equity",
    "excess_returns",
    "generate_report",
    "information_ratio",
    "max_drawdown",
    "pair_trades",
    "print_report",
    "profit_factor",
    "sharpe_ratio",
    "sortino_ratio",
    "trade_summary",
    "total_return",
    "win_rate",
]
