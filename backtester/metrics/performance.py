"""Performance metrics implemented from first principles."""

from __future__ import annotations

import math

import pandas as pd

from backtester.engine.backtest import BacktestResult
from backtester.portfolio.order import Side, Trade
from backtester.metrics.trades import trade_summary


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


def rolling_sharpe_ratio(
    returns: pd.Series,
    window: int = 63,
    risk_free_rate: float = 0.0,
) -> pd.Series:
    """Return annualized rolling Sharpe ratios for a return series."""
    if returns.empty:
        return pd.Series(index=returns.index, dtype="float64", name="rolling_sharpe")
    daily_rf = risk_free_rate / 252
    excess = returns - daily_rf
    rolling_std = excess.rolling(window).std()
    values = (excess.rolling(window).mean() / rolling_std) * math.sqrt(252)
    return pd.Series(values.replace([float("inf"), float("-inf")], 0.0).fillna(0.0), index=returns.index, name="rolling_sharpe")


def rolling_volatility(returns: pd.Series, window: int = 63) -> pd.Series:
    """Return annualized rolling volatility for a return series."""
    if returns.empty:
        return pd.Series(index=returns.index, dtype="float64", name="rolling_volatility")
    values = returns.rolling(window).std() * math.sqrt(252)
    return pd.Series(values.fillna(0.0), index=returns.index, name="rolling_volatility")


def rolling_drawdown(equity_curve: pd.Series, window: int = 63) -> pd.Series:
    """Return drawdown from the rolling window high as negative decimals."""
    if equity_curve.empty:
        return pd.Series(index=equity_curve.index, dtype="float64", name="rolling_drawdown")
    rolling_max = equity_curve.rolling(window, min_periods=1).max()
    safe_rolling_max = rolling_max.mask(rolling_max == 0)
    values = ((equity_curve - safe_rolling_max) / safe_rolling_max).fillna(0.0)
    return pd.Series(values, index=equity_curve.index, name="rolling_drawdown")


def drawdown_duration_days(equity_curve: pd.Series) -> int:
    """Return the longest consecutive number of bars spent below a prior high."""
    if equity_curve.empty:
        return 0
    drawdown = rolling_drawdown(equity_curve, window=len(equity_curve))
    longest = 0
    current = 0
    for value in drawdown:
        if float(value) < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def best_worst_day(returns: pd.Series) -> tuple[float, float]:
    """Return best and worst single-period returns."""
    if returns.empty:
        return (0.0, 0.0)
    return (float(returns.max()), float(returns.min()))


def monthly_returns(equity_curve: pd.Series) -> pd.DataFrame:
    """Return calendar monthly returns with year, month, and return columns."""
    if len(equity_curve) < 2:
        return pd.DataFrame(columns=["year", "month", "return"])
    monthly_equity = equity_curve.resample("ME").last()
    monthly = monthly_equity.pct_change().dropna()
    return pd.DataFrame(
        {
            "year": monthly.index.year.astype(int),
            "month": monthly.index.month.astype(int),
            "return": monthly.to_numpy(dtype=float),
        }
    )


def value_at_risk(returns: pd.Series, confidence: float = 0.95) -> float:
    """Return historical Value at Risk as a negative return threshold."""
    if returns.empty:
        return 0.0
    quantile = 1 - confidence
    return float(returns.quantile(quantile))


def conditional_value_at_risk(returns: pd.Series, confidence: float = 0.95) -> float:
    """Return average return beyond the historical VaR threshold."""
    if returns.empty:
        return 0.0
    threshold = value_at_risk(returns, confidence=confidence)
    tail = returns[returns <= threshold]
    if tail.empty:
        return threshold
    return float(tail.mean())


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


def buy_and_hold_equity(
    price_data: pd.DataFrame,
    initial_cash: float,
    price_column: str = "close",
    commission_rate: float = 0.0,
    slippage_bps: float = 0.0,
) -> pd.Series:
    """Return a simple buy-and-hold benchmark equity curve."""
    if initial_cash <= 0:
        msg = "initial_cash must be positive."
        raise ValueError(msg)
    if price_data.empty:
        return pd.Series(index=price_data.index, dtype="float64", name="benchmark_equity")

    first_close = float(price_data[price_column].iloc[0])
    if first_close <= 0:
        msg = "first benchmark price must be positive."
        raise ValueError(msg)
    entry_price = first_close * (1 + slippage_bps / 10_000)
    max_quantity = int(initial_cash // entry_price)
    commission = commission_rate * max_quantity
    while max_quantity > 0 and max_quantity * entry_price + commission > initial_cash:
        max_quantity -= 1
        commission = commission_rate * max_quantity
    remaining_cash = initial_cash - max_quantity * entry_price - commission
    values = remaining_cash + max_quantity * price_data[price_column].astype(float)
    return pd.Series(values.to_numpy(dtype=float), index=price_data.index, name="benchmark_equity")


def excess_returns(strategy_equity: pd.Series, benchmark_equity: pd.Series) -> pd.Series:
    """Return aligned strategy daily returns minus benchmark daily returns."""
    aligned = pd.concat(
        [strategy_equity.rename("strategy"), benchmark_equity.rename("benchmark")],
        axis=1,
        join="inner",
    )
    returns = aligned.pct_change().dropna()
    excess = returns["strategy"] - returns["benchmark"]
    return pd.Series(excess, index=excess.index, name="excess_returns")


def alpha_beta(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float = 0.0,
) -> tuple[float, float]:
    """Return annualized alpha and beta versus benchmark returns."""
    aligned = pd.concat(
        [strategy_returns.rename("strategy"), benchmark_returns.rename("benchmark")],
        axis=1,
        join="inner",
    ).dropna()
    if len(aligned) < 2:
        return (0.0, 0.0)

    daily_rf = risk_free_rate / 252
    excess_strategy = aligned["strategy"] - daily_rf
    excess_benchmark = aligned["benchmark"] - daily_rf
    benchmark_variance = float(excess_benchmark.var())
    if benchmark_variance == 0.0 or math.isnan(benchmark_variance):
        return (0.0, 0.0)

    beta = float(excess_strategy.cov(excess_benchmark) / benchmark_variance)
    alpha_daily = float(excess_strategy.mean()) - beta * float(excess_benchmark.mean())
    return (alpha_daily * 252, beta)


def information_ratio(strategy_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Return annualized information ratio versus benchmark returns."""
    aligned = pd.concat(
        [strategy_returns.rename("strategy"), benchmark_returns.rename("benchmark")],
        axis=1,
        join="inner",
    ).dropna()
    if aligned.empty:
        return 0.0
    active_returns = aligned["strategy"] - aligned["benchmark"]
    tracking_error = float(active_returns.std())
    if tracking_error == 0.0 or math.isnan(tracking_error):
        return 0.0
    return float(active_returns.mean()) / tracking_error * math.sqrt(252)


def generate_report(
    result: BacktestResult,
    risk_free_rate: float = 0.0,
    benchmark_equity: pd.Series | None = None,
) -> dict[str, object]:
    """Generate a stable dictionary of performance metrics for a backtest result."""
    returns = result.equity_curve.pct_change().dropna()
    total_return_value = total_return(result.initial_value, result.final_value)
    report: dict[str, object] = {
        "strategy": result.strategy_name,
        "initial_value": result.initial_value,
        "final_value": result.final_value,
        "total_return": total_return_value,
        "annualized_return": annualized_return(result.equity_curve),
        "sharpe_ratio": sharpe_ratio(returns, risk_free_rate=risk_free_rate),
        "sortino_ratio": sortino_ratio(returns, risk_free_rate=risk_free_rate),
        "max_drawdown": max_drawdown(result.equity_curve),
        "win_rate": win_rate(result.trades),
        "profit_factor": profit_factor(result.trades),
        "total_trades": len(result.trades),
        "trade_summary": trade_summary(result.trades),
    }
    if benchmark_equity is not None:
        benchmark_returns = benchmark_equity.pct_change().dropna()
        alpha, beta = alpha_beta(returns, benchmark_returns, risk_free_rate=risk_free_rate)
        benchmark_total = total_return(float(benchmark_equity.iloc[0]), float(benchmark_equity.iloc[-1])) if len(benchmark_equity) >= 2 else 0.0
        report.update(
            {
                "benchmark_total_return": benchmark_total,
                "excess_total_return": total_return_value - benchmark_total,
                "alpha": alpha,
                "beta": beta,
                "information_ratio": information_ratio(returns, benchmark_returns),
            }
        )
    return report


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
