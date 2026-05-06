"""Benchmark BacktestEngine throughput.

Run synthetic data by default:
    python benchmarks/benchmark_backtest.py

Run a real DataLoader-backed benchmark:
    python benchmarks/benchmark_backtest.py --real --ticker AAPL
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from time import perf_counter

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtester.data.loader import DataLoader
from backtester.engine import BacktestConfig, BacktestEngine, PositionSizeMethod
from backtester.strategy import MomentumStrategy


class SyntheticLoader(DataLoader):
    """DataLoader-compatible synthetic data source for offline benchmarking."""

    def __init__(self, bars: int) -> None:
        self._data = make_synthetic_data(bars)

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        del ticker, start, end
        return self._data.copy()


def make_synthetic_data(bars: int) -> pd.DataFrame:
    dates = pd.date_range("2010-01-01", periods=bars, freq="B", name="date")
    closes = [100.0 + index * 0.01 + (index % 31 - 15) * 0.08 for index in range(bars)]
    return pd.DataFrame(
        {
            "open": closes,
            "high": [close * 1.01 for close in closes],
            "low": [close * 0.99 for close in closes],
            "close": closes,
            "volume": [100_000] * bars,
        },
        index=dates,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark Backtester throughput.")
    parser.add_argument("--real", action="store_true", help="Use DataLoader/yfinance instead of synthetic data.")
    parser.add_argument("--ticker", default="AAPL")
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default="2024-01-01")
    parser.add_argument("--bars", type=int, default=2_500)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    loader = DataLoader() if args.real else SyntheticLoader(args.bars)
    config = BacktestConfig(
        ticker=args.ticker,
        start_date=args.start,
        end_date=args.end,
        commission_rate=0.0,
        slippage_bps=0.0,
        position_size_method=PositionSizeMethod.FIXED_DOLLAR,
        position_size_value=10_000.0,
    )
    strategy = MomentumStrategy(fast_window=10, slow_window=50)
    engine = BacktestEngine(loader=loader, strategy=strategy, config=config)

    start_time = perf_counter()
    result = engine.run()
    elapsed = perf_counter() - start_time
    bars_processed = len(result.equity_curve)
    throughput = bars_processed / elapsed if elapsed > 0 else float("inf")

    print(f"mode: {'real' if args.real else 'synthetic'}")
    print(f"elapsed_seconds: {elapsed:.6f}")
    print(f"bars_processed: {bars_processed}")
    print(f"bars_per_second: {throughput:.2f}")
    print(f"trades: {len(result.trades)}")
    print(f"final_value: {result.final_value:.2f}")


if __name__ == "__main__":
    main()

