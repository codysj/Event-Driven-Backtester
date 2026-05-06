"""Performance metrics implemented from first principles."""

from __future__ import annotations

import math

import pandas as pd

from backtester.engine.backtest import BacktestResult
from backtester.portfolio.order import Side, Trade


def total_return(initial_value: float, final_value: float) -> float:
    """Return total return as ``(final - initial) / initial``."""
    if initial_value <= 0:
        msg = "initial_value must be positive."
        raise ValueError(msg)
    return (final_value - initial_value) / initial_value


def annualized_return(equity_curve: pd.Series) -> float:
    """Return annualized return using elapsed intervals as trading days.

    A curve with N points contains N - 1 return intervals, so this function
    uses ``len(equity_curve) - 1`` trading days.
    """
    if len(equity_curve) < 2:
        return 0.0

    first_equity = float(equity_curve.iloc[0])
    last_equity = float(equity_curve.iloc[-1])
    if first_equity <= 0:
        msg = "first equity value must be positive."
        raise ValueError(msg)

    total = (last_equity - first_equity) / first_equity
    if total <= -1.0:
        return -1.0

    trading_days = len(equity_curve) - 1
    n_years = trading_days / 252
    return float((1 + total) ** (1 / n_years) - 1)


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Return annualized Sharpe ratio using pandas sample standard deviation."""
    if returns.empty:
        return 0.0

    daily_excess_returns = returns - (risk_free_rate / 252)
    std = float(daily_excess_returns.std())
    if std == 0.0 or math.isnan(std):
        return 0.0

    return float(daily_excess_returns.mean()) / std * math.sqrt(252)


def sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Return annualized Sortino ratio using downside sample std deviation."""
    if returns.empty:
        return 0.0

    daily_excess_returns = returns - (risk_free_rate / 252)
    downside_returns = daily_excess_returns[daily_excess_returns < 0]
    if downside_returns.empty:
        return 0.0

    downside_std = float(downside_returns.std())
    if downside_std == 0.0 or math.isnan(downside_std):
        return 0.0

    return float(daily_excess_returns.mean()) / downside_std * math.sqrt(252)


def max_drawdown(equity_curve: pd.Series) -> float:
    """Return the maximum drawdown as a negative decimal."""
    if equity_curve.empty:
        return 0.0

    rolling_max = equity_curve.cummax()
    safe_rolling_max = rolling_max.mask(rolling_max == 0)
    drawdown = (equity_curve - safe_rolling_max) / safe_rolling_max
    min_drawdown = drawdown.min(skipna=True)
    if pd.isna(min_drawdown):
        return 0.0
    return float(min_drawdown)


def win_rate(trades: list[Trade]) -> float:
    """Return the share of sequential buy/sell pairs with sell price > buy price."""
    pairs = _paired_trades(trades)
    if not pairs:
        return 0.0

    wins = sum(1 for buy, sell in pairs if sell.price > buy.price)
    return wins / len(pairs)


def profit_factor(trades: list[Trade]) -> float:
    """Return gross profits divided by absolute gross losses."""
    pairs = _paired_trades(trades)
    if not pairs:
        return 0.0

    gross_profit = 0.0
    gross_loss = 0.0
    for buy, sell in pairs:
        paired_quantity = min(buy.quantity, sell.quantity)
        pnl = (sell.price - buy.price) * paired_quantity - buy.commission - sell.commission
        if pnl > 0:
            gross_profit += pnl
        elif pnl < 0:
            gross_loss += abs(pnl)

    if gross_loss == 0.0:
        if gross_profit > 0.0:
            return float("inf")
        return 0.0
    return gross_profit / gross_loss


def generate_report(result: BacktestResult, risk_free_rate: float = 0.0) -> dict[str, object]:
    """Generate a stable dictionary of performance metrics for a backtest result."""
    returns = result.equity_curve.pct_change().dropna()
    return {
        "strategy": result.strategy_name,
        "initial_value": result.initial_value,
        "final_value": result.final_value,
        "total_return": total_return(result.initial_value, result.final_value),
        "annualized_return": annualized_return(result.equity_curve),
        "sharpe_ratio": sharpe_ratio(returns, risk_free_rate=risk_free_rate),
        "sortino_ratio": sortino_ratio(returns, risk_free_rate=risk_free_rate),
        "max_drawdown": max_drawdown(result.equity_curve),
        "win_rate": win_rate(result.trades),
        "profit_factor": profit_factor(result.trades),
        "total_trades": len(result.trades),
    }


def print_report(report: dict[str, object]) -> None:
    """Pretty-print a generated performance report."""
    print("Backtest Performance Report")
    print("===========================")
    for key, value in report.items():
        label = key.replace("_", " ").title()
        if isinstance(value, float):
            print(f"{label}: {value:.4f}")
        else:
            print(f"{label}: {value}")


def _paired_trades(trades: list[Trade]) -> list[tuple[Trade, Trade]]:
    pairs: list[tuple[Trade, Trade]] = []
    pending_buy: Trade | None = None

    for trade in trades:
        if trade.side is Side.BUY and pending_buy is None:
            pending_buy = trade
        elif trade.side is Side.SELL and pending_buy is not None:
            pairs.append((pending_buy, trade))
            pending_buy = None

    return pairs
