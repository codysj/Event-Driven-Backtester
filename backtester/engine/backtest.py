"""Core event-driven backtest loop."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from backtester.data.loader import DataLoader
from backtester.engine.config import BacktestConfig, PositionSizeMethod
from backtester.portfolio import Order, Portfolio, Side, Trade
from backtester.strategy import Signal, Strategy


@dataclass
class BacktestResult:
    """Output of a completed backtest run."""

    config: BacktestConfig
    strategy_name: str
    equity_curve: pd.Series
    trades: list[Trade]
    final_value: float
    initial_value: float


class BacktestEngine:
    """Compose data, strategy, and portfolio components into a backtest."""

    def __init__(
        self,
        loader: DataLoader,
        strategy: Strategy,
        config: BacktestConfig,
    ) -> None:
        self._loader = loader
        self._strategy = strategy
        self._config = config

    def run(self) -> BacktestResult:
        data = self._loader.fetch(
            self._config.ticker,
            self._config.start_date,
            self._config.end_date,
        )
        portfolio = Portfolio(
            initial_cash=self._config.initial_cash,
            commission_rate=self._config.commission_rate,
        )

        for i in range(len(data)):
            current_bar = data.iloc[i]
            timestamp = self._timestamp_at(data, i)
            current_price = float(current_bar["close"])

            # This slice is intentionally incremental to prevent look-ahead
            # bias: the strategy sees bars 0 through i, never future bars.
            historical_data = data.iloc[: i + 1]
            signal = self._strategy.generate_signal(historical_data)
            order = self._signal_to_order(
                signal,
                self._config.ticker,
                timestamp,
                current_price,
                portfolio,
            )
            if order is not None:
                portfolio.execute_order(
                    order,
                    current_price,
                    slippage_bps=self._config.slippage_bps,
                )

            portfolio.record_equity(timestamp, {self._config.ticker: current_price})

        final_close = float(data.iloc[-1]["close"])
        return BacktestResult(
            config=self._config,
            strategy_name=self._strategy.name,
            equity_curve=portfolio.get_equity_curve(),
            trades=portfolio.trade_history,
            final_value=portfolio.total_value({self._config.ticker: final_close}),
            initial_value=self._config.initial_cash,
        )

    def _signal_to_order(
        self,
        signal: Signal,
        ticker: str,
        timestamp: datetime,
        current_price: float,
        portfolio: Portfolio,
    ) -> Order | None:
        if signal is Signal.HOLD:
            return None

        if signal is Signal.BUY:
            quantity = self._calculate_buy_quantity(current_price, portfolio.cash)
            if quantity <= 0:
                return None
            return Order(ticker=ticker, side=Side.BUY, quantity=quantity, timestamp=timestamp)

        position = portfolio.get_position(ticker)
        if position is None:
            return None
        return Order(ticker=ticker, side=Side.SELL, quantity=position.quantity, timestamp=timestamp)

    def _calculate_buy_quantity(self, price: float, available_cash: float) -> int:
        if price <= 0:
            return 0

        if self._config.position_size_method is PositionSizeMethod.ALL_IN:
            return int(available_cash // price)
        if self._config.position_size_method is PositionSizeMethod.FIXED_DOLLAR:
            return int(self._config.position_size_value // price)
        return int(self._config.position_size_value)

    def _timestamp_at(self, data: pd.DataFrame, index: int) -> datetime:
        timestamp = data.index[index]
        if isinstance(timestamp, datetime):
            return timestamp
        return pd.Timestamp(timestamp).to_pydatetime()

