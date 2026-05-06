"""Matplotlib chart helpers for backtest results."""

from __future__ import annotations

from pathlib import Path

from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter
import pandas as pd

from backtester.engine.backtest import BacktestResult
from backtester.portfolio.order import Side, Trade


def plot_equity_curve(
    result: BacktestResult,
    benchmark_equity: pd.Series | None = None,
    save_path: str | None = None,
) -> None:
    """Plot a portfolio equity curve with an optional benchmark overlay."""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(
        _date_axis_values(result.equity_curve.index),
        _series_values(result.equity_curve),
        label=result.strategy_name,
    )
    if benchmark_equity is not None:
        ax.plot(
            _date_axis_values(benchmark_equity.index),
            _series_values(benchmark_equity),
            label="Benchmark",
        )

    ax.set_title("Portfolio Equity Curve")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value ($)")
    ax.yaxis.set_major_formatter(FuncFormatter(_format_currency))
    ax.grid(alpha=0.3)
    ax.legend()
    _finish_figure(fig, save_path)


def plot_drawdown(
    equity_curve: pd.Series,
    save_path: str | None = None,
) -> None:
    """Plot an underwater drawdown chart."""
    fig, ax = plt.subplots(figsize=(12, 4))
    if equity_curve.empty:
        drawdown = pd.Series(index=equity_curve.index, dtype="float64")
    else:
        rolling_max = equity_curve.cummax()
        safe_rolling_max = rolling_max.mask(rolling_max == 0)
        drawdown = ((equity_curve - safe_rolling_max) / safe_rolling_max).fillna(0.0)

    x_values = _date_axis_values(drawdown.index)
    y_values = _series_values(drawdown)
    ax.plot(x_values, y_values, color="red", label="Drawdown")
    ax.fill_between(x_values, y_values, 0.0, color="red", alpha=0.25)
    ax.set_title("Drawdown")
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))
    ax.grid(alpha=0.3)
    _finish_figure(fig, save_path)


def plot_trades(
    price_data: pd.DataFrame,
    trades: list[Trade],
    save_path: str | None = None,
) -> None:
    """Plot close prices with buy and sell trade markers."""
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(_date_axis_values(price_data.index), _series_values(price_data["close"]), label="Close")

    buy_trades = [trade for trade in trades if trade.side is Side.BUY]
    sell_trades = [trade for trade in trades if trade.side is Side.SELL]
    if buy_trades:
        ax.scatter(
            [trade.timestamp.isoformat() for trade in buy_trades],
            [trade.price for trade in buy_trades],
            marker="^",
            color="green",
            label="Buy",
        )
    if sell_trades:
        ax.scatter(
            [trade.timestamp.isoformat() for trade in sell_trades],
            [trade.price for trade in sell_trades],
            marker="v",
            color="red",
            label="Sell",
        )

    ax.set_title("Trades")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price ($)")
    ax.grid(alpha=0.3)
    ax.legend()
    _finish_figure(fig, save_path)


def plot_strategy_comparison(
    results: list[BacktestResult],
    save_path: str | None = None,
) -> None:
    """Plot multiple strategy equity curves on one axis."""
    fig, ax = plt.subplots(figsize=(12, 6))
    for result in results:
        ax.plot(
            _date_axis_values(result.equity_curve.index),
            _series_values(result.equity_curve),
            label=result.strategy_name,
        )

    ax.set_title("Strategy Comparison")
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value ($)")
    ax.yaxis.set_major_formatter(FuncFormatter(_format_currency))
    ax.grid(alpha=0.3)
    if results:
        ax.legend()
    _finish_figure(fig, save_path)


def _finish_figure(fig: Figure, save_path: str | None) -> None:
    fig.tight_layout()
    try:
        if save_path is not None:
            path = Path(save_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(path, dpi=150)
        else:
            plt.show()
    finally:
        plt.close(fig)


def _format_currency(value: float, position: int) -> str:
    del position
    return f"${value:,.0f}"


def _date_axis_values(index: pd.Index) -> list[str]:
    return [timestamp.isoformat() for timestamp in pd.to_datetime(index)]


def _series_values(series: pd.Series) -> list[float]:
    return [float(value) for value in series.to_list()]
