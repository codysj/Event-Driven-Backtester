"""Pydantic schemas for the Backtester API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from backtester.engine import PositionSizeMethod


StrategyId = Literal["momentum", "mean_reversion"]
ParameterType = Literal["integer", "number"]


class StrategyParameterSchema(BaseModel):
    """Metadata for one configurable strategy parameter."""

    name: str
    type: ParameterType
    default: int | float
    min: int | float
    label: str


class StrategyMetadata(BaseModel):
    """Strategy metadata exposed to the frontend."""

    id: StrategyId
    name: str
    description: str
    parameters: list[StrategyParameterSchema]


class StrategiesResponse(BaseModel):
    """Response containing available strategies."""

    strategies: list[StrategyMetadata]


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str


class BacktestRequest(BaseModel):
    """Backtest request submitted by the frontend."""

    ticker: str = Field(..., min_length=1)
    start_date: str = Field(..., min_length=1)
    end_date: str = Field(..., min_length=1)
    strategy: StrategyId
    initial_cash: float = Field(default=100_000.0, gt=0)
    commission_rate: float = Field(default=0.001, ge=0)
    slippage_bps: float = Field(default=5.0, ge=0)
    position_size_method: PositionSizeMethod = PositionSizeMethod.FIXED_DOLLAR
    position_size_value: float = Field(default=10_000.0, gt=0)
    benchmark: bool = True
    parameters: dict[str, int | float] = Field(default_factory=dict)

    @field_validator("ticker")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()

    @model_validator(mode="after")
    def validate_strategy_parameters(self) -> "BacktestRequest":
        params = self.parameters
        if self.strategy == "momentum":
            fast_window = int(params.get("fast_window", 10))
            slow_window = int(params.get("slow_window", 50))
            if fast_window <= 0:
                msg = "fast_window must be positive."
                raise ValueError(msg)
            if slow_window <= 0:
                msg = "slow_window must be positive."
                raise ValueError(msg)
            if fast_window >= slow_window:
                msg = "fast_window must be less than slow_window."
                raise ValueError(msg)
        if self.strategy == "mean_reversion":
            window = int(params.get("window", 20))
            num_std = float(params.get("num_std", 2.0))
            if window <= 0:
                msg = "window must be positive."
                raise ValueError(msg)
            if num_std <= 0:
                msg = "num_std must be positive."
                raise ValueError(msg)
        return self


class BacktestSummary(BaseModel):
    """Summary values shown above the dashboard charts."""

    strategy_name: str
    ticker: str
    initial_value: float
    final_value: float
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    alpha: float | None = None
    beta: float | None = None
    information_ratio: float | None = None
    total_trades: int


class SeriesPoint(BaseModel):
    """Date/value point for line charts."""

    date: str
    value: float


class PricePoint(BaseModel):
    """Close price point for price charts."""

    date: str
    close: float


class TradeSchema(BaseModel):
    """Executed trade exposed to the frontend."""

    ticker: str
    side: str
    quantity: int
    price: float
    commission: float
    timestamp: str


class BacktestSeries(BaseModel):
    """All chart series returned for a backtest."""

    equity: list[SeriesPoint]
    benchmark: list[SeriesPoint]
    drawdown: list[SeriesPoint]
    price: list[PricePoint]


class BacktestResponse(BaseModel):
    """Backtest response consumed by the dashboard."""

    config: dict[str, object]
    summary: BacktestSummary
    series: BacktestSeries
    trades: list[TradeSchema]


class ErrorResponse(BaseModel):
    """Readable API error response."""

    detail: str

