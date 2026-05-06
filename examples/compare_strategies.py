"""Compare two strategies on the same synthetic dataset."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtester.data.loader import DataLoader
from backtester.engine import BacktestConfig, BacktestEngine, PositionSizeMethod
from backtester.metrics import generate_report
from backtester.strategy import MeanReversionStrategy, MomentumStrategy, Strategy


class SyntheticLoader(DataLoader):
    def __init__(self) -> None:
        dates = pd.date_range("2020-01-01", periods=160, freq="B", name="date")
        closes = [100.0 + (index % 40 - 20) * 0.7 + index * 0.04 for index in range(160)]
        self._data = pd.DataFrame(
            {
                "open": closes,
                "high": [close * 1.01 for close in closes],
                "low": [close * 0.99 for close in closes],
                "close": closes,
                "volume": [100_000] * len(closes),
            },
            index=dates,
        )

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        del ticker, start, end
        return self._data.copy()


def run_strategy(strategy: Strategy) -> None:
    config = BacktestConfig(
        ticker="SYNTH",
        start_date="2020-01-01",
        end_date="2020-08-31",
        position_size_method=PositionSizeMethod.FIXED_DOLLAR,
        position_size_value=10_000.0,
    )
    result = BacktestEngine(loader=SyntheticLoader(), strategy=strategy, config=config).run()
    report = generate_report(result)
    strategy_name = result.strategy_name.encode("ascii", errors="replace").decode("ascii")
    print(f"{strategy_name}: final={result.final_value:.2f}, trades={len(result.trades)}, total_return={report['total_return']:.4f}")


def main() -> None:
    run_strategy(MomentumStrategy(fast_window=10, slow_window=30))
    run_strategy(MeanReversionStrategy(window=20, num_std=1.5))


if __name__ == "__main__":
    main()
