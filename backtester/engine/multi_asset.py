"""Multi-asset event-driven backtest engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import cast

import pandas as pd

from backtester.data.loader import DataLoader
from backtester.engine.config import MultiAssetBacktestConfig
from backtester.engine.sizing import calculate_buy_quantity
from backtester.portfolio import Order, Portfolio, Side, Trade
from backtester.strategy import MultiAssetStrategy, Signal


@dataclass
class MultiAssetBacktestResult:
    """Output of a completed multi-asset backtest."""

    config: MultiAssetBacktestConfig
    strategy_name: str
    equity_curve: pd.Series
    trades: list[Trade]
    final_value: float
    initial_value: float
    price_data: dict[str, pd.DataFrame]
    benchmark_equity: pd.Series | None = None


class MultiAssetBacktestEngine:
    """Compose loader, multi-asset strategy, and portfolio over many tickers.

    DataFrames are aligned on the intersection of all trading dates. Signals are
    processed in config ticker order, so competing BUY orders may consume cash
    before later tickers are reached. In multi-asset mode, ALL_IN uses all
    currently available cash for each BUY as it is processed.
    """

    def __init__(
        self,
        loader: DataLoader,
        strategy: MultiAssetStrategy,
        config: MultiAssetBacktestConfig,
    ) -> None:
        self._loader = loader
        self._strategy = strategy
        self._config = config

    def run(self) -> MultiAssetBacktestResult:
        aligned_data = self._load_and_align_data()
        portfolio = Portfolio(
            initial_cash=self._config.initial_cash,
            commission_rate=self._config.commission_rate,
        )
        self._strategy.precompute(aligned_data)
        close_arrays = {
            ticker: frame["close"].to_numpy(dtype=float)
            for ticker, frame in aligned_data.items()
        }
        shared_index = next(iter(aligned_data.values())).index
        timestamps = pd.to_datetime(shared_index).to_pydatetime()

        for current_index in range(len(shared_index)):
            timestamp = cast(datetime, timestamps[current_index])
            current_prices = {
                ticker: float(close_arrays[ticker][current_index])
                for ticker in self._config.tickers
            }
            signals = self._strategy.generate_signals(aligned_data, current_index)

            for ticker in self._config.tickers:
                order = self._signal_to_order(
                    signal=signals.get(ticker, Signal.HOLD),
                    ticker=ticker,
                    timestamp=timestamp,
                    current_price=current_prices[ticker],
                    current_prices=current_prices,
                    portfolio=portfolio,
                    data=aligned_data[ticker],
                    current_index=current_index,
                )
                if order is not None:
                    portfolio.execute_order(
                        order,
                        current_prices[ticker],
                        slippage_bps=self._config.slippage_bps,
                    )

            portfolio.record_equity(timestamp, current_prices)

        final_prices = {
            ticker: float(close_arrays[ticker][-1])
            for ticker in self._config.tickers
        }
        return MultiAssetBacktestResult(
            config=self._config,
            strategy_name=self._strategy.name,
            equity_curve=portfolio.get_equity_curve(),
            trades=portfolio.trade_history,
            final_value=portfolio.total_value(final_prices),
            initial_value=self._config.initial_cash,
            price_data={ticker: frame.copy() for ticker, frame in aligned_data.items()},
        )

    def _load_and_align_data(self) -> dict[str, pd.DataFrame]:
        raw_data = {
            ticker: self._loader.fetch(ticker, self._config.start_date, self._config.end_date)
            for ticker in self._config.tickers
        }
        common_index: pd.Index | None = None
        for frame in raw_data.values():
            common_index = frame.index if common_index is None else common_index.intersection(frame.index)
        if common_index is None or len(common_index) == 0:
            msg = "No common dates found across requested tickers."
            raise ValueError(msg)

        common_index = common_index.sort_values()
        return {
            ticker: frame.loc[common_index].sort_index().copy()
            for ticker, frame in raw_data.items()
        }

    def _signal_to_order(
        self,
        *,
        signal: Signal,
        ticker: str,
        timestamp: datetime,
        current_price: float,
        current_prices: dict[str, float],
        portfolio: Portfolio,
        data: pd.DataFrame,
        current_index: int,
    ) -> Order | None:
        if signal is Signal.HOLD:
            return None
        if signal is Signal.BUY:
            quantity = calculate_buy_quantity(
                config=self._config,
                price=current_price,
                available_cash=portfolio.cash,
                portfolio_value=portfolio.total_value(current_prices),
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
