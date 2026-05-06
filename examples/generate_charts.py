"""Generate example PNG charts in docs/ using synthetic data."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtester.data.loader import DataLoader
from backtester.engine import BacktestConfig, BacktestEngine, PositionSizeMethod
from backtester.strategy import MeanReversionStrategy, MomentumStrategy
from backtester.viz import plot_drawdown, plot_equity_curve, plot_strategy_comparison, plot_trades


class SyntheticLoader(DataLoader):
    def __init__(self) -> None:
        dates = pd.date_range("2020-01-01", periods=160, freq="B", name="date")
        closes = [100.0 + (index % 40 - 20) * 0.7 + index * 0.04 for index in range(160)]
        self.data = pd.DataFrame(
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
        return self.data.copy()


def main() -> None:
    docs = ROOT / "docs"
    config = BacktestConfig(
        ticker="SYNTH",
        start_date="2020-01-01",
        end_date="2020-08-31",
        position_size_method=PositionSizeMethod.FIXED_DOLLAR,
        position_size_value=10_000.0,
    )
    momentum = BacktestEngine(SyntheticLoader(), MomentumStrategy(10, 30), config).run()
    mean_reversion = BacktestEngine(SyntheticLoader(), MeanReversionStrategy(20, 1.5), config).run()
    price_data = SyntheticLoader().fetch("SYNTH", "2020-01-01", "2020-08-31")

    plot_equity_curve(momentum, save_path=str(docs / "equity_curve.png"))
    plot_drawdown(momentum.equity_curve, save_path=str(docs / "drawdown.png"))
    plot_trades(price_data, momentum.trades, save_path=str(docs / "trades.png"))
    plot_strategy_comparison([momentum, mean_reversion], save_path=str(docs / "comparison.png"))
    print(f"charts written to {docs}")


if __name__ == "__main__":
    main()

