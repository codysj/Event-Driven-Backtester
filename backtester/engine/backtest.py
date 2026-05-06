"""Core event-driven backtest loop."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import cast

import pandas as pd

from backtester.data.loader import DataLoader
from backtester.engine.config import BacktestConfig
from backtester.engine.sizing import calculate_buy_quantity
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
        self._strategy.precompute(data)
        close_array = data["close"].to_numpy(dtype=float)
        timestamps = pd.to_datetime(data.index).to_pydatetime()

        for i in range(len(data)):
            timestamp = cast(datetime, timestamps[i])
            current_price = float(close_array[i])

            # Stage 7 avoids per-bar DataFrame copies. Strategies receive the
            # full DataFrame and must honor current_index as the look-ahead
            # boundary.
            signal = self._strategy.generate_signal(data, current_index=i)
            order = self._signal_to_order(
                signal,
                self._config.ticker,
                timestamp,
                current_price,
                portfolio,
                data,
                i,
            )
            if order is not None:
                portfolio.execute_order(
                    order,
                    current_price,
                    slippage_bps=self._config.slippage_bps,
                )

            portfolio.record_equity(timestamp, {self._config.ticker: current_price})

        final_close = float(close_array[-1])
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
        data: pd.DataFrame,
        current_index: int,
    ) -> Order | None:
        if signal is Signal.HOLD:
            return None

        if signal is Signal.BUY:
            portfolio_value = portfolio.total_value({ticker: current_price})
            quantity = calculate_buy_quantity(
                config=self._config,
                price=current_price,
                available_cash=portfolio.cash,
                portfolio_value=portfolio_value,
                data=data,
                current_index=current_index,
            )
            if quantity <= 0:
                return None
            return Order(ticker=ticker, side=Side.BUY, quantity=quantity, timestamp=timestamp)

        position = portfolio.get_position(ticker)
        if position is None:
            return None
        return Order(ticker=ticker, side=Side.SELL, quantity=position.quantity, timestamp=timestamp)
