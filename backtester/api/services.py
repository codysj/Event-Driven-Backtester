"""Service helpers for the FastAPI layer."""

from __future__ import annotations

import math

import pandas as pd

from backtester.api.schemas import (
    BacktestRequest,
    BacktestResponse,
    BacktestSeries,
    BacktestSummary,
    PricePoint,
    SeriesPoint,
    StrategyMetadata,
    StrategyParameterSchema,
    TradeSchema,
)
from backtester.data.loader import DataLoader
from backtester.engine import BacktestConfig, BacktestEngine
from backtester.metrics import buy_and_hold_equity, generate_report
from backtester.portfolio import Trade
from backtester.strategy import MeanReversionStrategy, MomentumStrategy, Strategy


def available_strategies() -> list[StrategyMetadata]:
    """Return supported strategy metadata for the frontend."""
    return [
        StrategyMetadata(
            id="momentum",
            name="Momentum SMA Crossover",
            description="Uses fast and slow moving average crossovers to generate buy/sell signals.",
            parameters=[
                StrategyParameterSchema(name="fast_window", type="integer", default=10, min=1, label="Fast Window"),
                StrategyParameterSchema(name="slow_window", type="integer", default=50, min=2, label="Slow Window"),
            ],
        ),
        StrategyMetadata(
            id="mean_reversion",
            name="Mean Reversion",
            description="Uses Bollinger-style bands to identify overextended prices.",
            parameters=[
                StrategyParameterSchema(name="window", type="integer", default=20, min=1, label="Window"),
                StrategyParameterSchema(name="num_std", type="number", default=2.0, min=0.1, label="Standard Deviations"),
            ],
        ),
    ]


def build_strategy(strategy_id: str, parameters: dict[str, int | float]) -> Strategy:
    """Build a Strategy instance from API request parameters."""
    if strategy_id == "momentum":
        return MomentumStrategy(
            fast_window=int(parameters.get("fast_window", 10)),
            slow_window=int(parameters.get("slow_window", 50)),
        )
    if strategy_id == "mean_reversion":
        return MeanReversionStrategy(
            window=int(parameters.get("window", 20)),
            num_std=float(parameters.get("num_std", 2.0)),
        )
    msg = f"Unsupported strategy: {strategy_id}"
    raise ValueError(msg)


def run_backtest_from_request(request: BacktestRequest) -> BacktestResponse:
    """Run a single-asset backtest and convert it into an API response."""
    loader = DataLoader()
    config = BacktestConfig(
        ticker=request.ticker,
        start_date=request.start_date,
        end_date=request.end_date,
        initial_cash=request.initial_cash,
        commission_rate=request.commission_rate,
        slippage_bps=request.slippage_bps,
        position_size_method=request.position_size_method,
        position_size_value=request.position_size_value,
    )
    strategy = build_strategy(request.strategy, request.parameters)
    result = BacktestEngine(loader=loader, strategy=strategy, config=config).run()
    price_data = loader.fetch(config.ticker, config.start_date, config.end_date)
    benchmark = buy_and_hold_equity(price_data, config.initial_cash) if request.benchmark else None
    report = generate_report(result, benchmark_equity=benchmark)

    return BacktestResponse(
        config={
            "ticker": config.ticker,
            "start_date": config.start_date,
            "end_date": config.end_date,
            "initial_cash": config.initial_cash,
            "commission_rate": config.commission_rate,
            "slippage_bps": config.slippage_bps,
            "position_size_method": config.position_size_method.value,
            "position_size_value": config.position_size_value,
            "strategy": request.strategy,
            "parameters": request.parameters,
            "benchmark": request.benchmark,
        },
        summary=BacktestSummary(
            strategy_name=result.strategy_name,
            ticker=config.ticker,
            initial_value=result.initial_value,
            final_value=result.final_value,
            total_return=_float_report_value(report, "total_return"),
            annualized_return=_float_report_value(report, "annualized_return"),
            sharpe_ratio=_float_report_value(report, "sharpe_ratio"),
            sortino_ratio=_float_report_value(report, "sortino_ratio"),
            max_drawdown=_float_report_value(report, "max_drawdown"),
            win_rate=_float_report_value(report, "win_rate"),
            profit_factor=_finite_float_report_value(report, "profit_factor"),
            alpha=_optional_report_value(report, "alpha"),
            beta=_optional_report_value(report, "beta"),
            information_ratio=_optional_report_value(report, "information_ratio"),
            total_trades=len(result.trades),
        ),
        series=BacktestSeries(
            equity=convert_equity_series(result.equity_curve),
            benchmark=convert_equity_series(benchmark) if benchmark is not None else [],
            drawdown=compute_drawdown_series(result.equity_curve),
            price=convert_price_data(price_data),
        ),
        trades=convert_trades(result.trades),
    )


def convert_equity_series(series: pd.Series) -> list[SeriesPoint]:
    """Convert a pandas Series into chart points."""
    return [
        SeriesPoint(date=pd.Timestamp(str(index)).date().isoformat(), value=float(value))
        for index, value in series.items()
    ]


def compute_drawdown_series(equity_curve: pd.Series) -> list[SeriesPoint]:
    """Compute drawdown chart points from an equity curve."""
    if equity_curve.empty:
        return []
    rolling_max = equity_curve.cummax()
    safe_rolling_max = rolling_max.mask(rolling_max == 0)
    drawdown = ((equity_curve - safe_rolling_max) / safe_rolling_max).fillna(0.0)
    return convert_equity_series(drawdown)


def convert_trades(trades: list[Trade]) -> list[TradeSchema]:
    """Convert engine trades into API trade records."""
    return [
        TradeSchema(
            ticker=trade.ticker,
            side=trade.side.value,
            quantity=trade.quantity,
            price=trade.price,
            commission=trade.commission,
            timestamp=trade.timestamp.date().isoformat(),
        )
        for trade in trades
    ]


def convert_price_data(data: pd.DataFrame) -> list[PricePoint]:
    """Convert price data into close-price chart points."""
    return [
        PricePoint(date=pd.Timestamp(str(index)).date().isoformat(), close=float(row["close"]))
        for index, row in data.iterrows()
    ]


def _float_report_value(report: dict[str, object], key: str) -> float:
    value = report[key]
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def _finite_float_report_value(report: dict[str, object], key: str) -> float:
    value = _float_report_value(report, key)
    if math.isfinite(value):
        return value
    return 0.0


def _optional_report_value(report: dict[str, object], key: str) -> float | None:
    if key not in report:
        return None
    value = _float_report_value(report, key)
    return value if math.isfinite(value) else None
