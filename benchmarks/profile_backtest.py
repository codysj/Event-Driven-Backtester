"""Profile a representative BacktestEngine run with cProfile."""

from __future__ import annotations

import argparse
import cProfile
from pathlib import Path
import pstats
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.benchmark_backtest import SyntheticLoader
from backtester.data.loader import DataLoader
from backtester.engine import BacktestConfig, BacktestEngine, PositionSizeMethod
from backtester.strategy import MomentumStrategy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile Backtester with cProfile.")
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
    engine = BacktestEngine(
        loader=loader,
        strategy=MomentumStrategy(fast_window=10, slow_window=50),
        config=config,
    )

    profiler = cProfile.Profile()
    profiler.enable()
    engine.run()
    profiler.disable()
    stats = pstats.Stats(profiler, stream=sys.stdout).sort_stats("cumtime")
    stats.print_stats(20)


if __name__ == "__main__":
    main()

