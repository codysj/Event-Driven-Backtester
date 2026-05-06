"""Synthetic multi-asset backtest demo."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtester.data.loader import DataLoader
from backtester.engine import MultiAssetBacktestConfig, MultiAssetBacktestEngine, PositionSizeMethod
from backtester.strategy import MomentumStrategy, SingleStrategyMultiAssetWrapper


class SyntheticMultiLoader(DataLoader):
    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        del start, end
        dates = pd.date_range("2020-01-01", periods=140, freq="B", name="date")
        offset = {"AAA": 0.0, "BBB": 8.0, "CCC": -5.0}.get(ticker, 0.0)
        closes = [100.0 + offset + index * 0.04 + (index % 20 - 10) * 0.3 for index in range(140)]
        return pd.DataFrame(
            {
                "open": closes,
                "high": [close * 1.01 for close in closes],
                "low": [close * 0.99 for close in closes],
                "close": closes,
                "volume": [100_000] * len(closes),
            },
            index=dates,
        )


def main() -> None:
    config = MultiAssetBacktestConfig(
        tickers=["AAA", "BBB", "CCC"],
        start_date="2020-01-01",
        end_date="2020-07-15",
        position_size_method=PositionSizeMethod.FIXED_DOLLAR,
        position_size_value=10_000.0,
    )
    strategy = SingleStrategyMultiAssetWrapper(lambda: MomentumStrategy(8, 25))
    result = MultiAssetBacktestEngine(SyntheticMultiLoader(), strategy, config).run()
    print(f"strategy: {result.strategy_name}")
    print(f"final_value: {result.final_value:.2f}")
    print(f"total_trades: {len(result.trades)}")
    print(f"equity_points: {len(result.equity_curve)}")


if __name__ == "__main__":
    main()
