"""One-command synthetic demo for reports, benchmark, and charts."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtester.data.loader import DataLoader
from backtester.engine import BacktestConfig, BacktestEngine, PositionSizeMethod
from backtester.metrics import buy_and_hold_equity, generate_report, print_report
from backtester.strategy import MomentumStrategy
from backtester.viz import plot_drawdown, plot_equity_curve, plot_trades


class SyntheticLoader(DataLoader):
    def __init__(self) -> None:
        dates = pd.date_range("2020-01-01", periods=180, freq="B", name="date")
        closes = [100.0 + index * 0.07 + (index % 30 - 15) * 0.45 for index in range(180)]
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


def main() -> None:
    loader = SyntheticLoader()
    config = BacktestConfig(
        ticker="SYNTH",
        start_date="2020-01-01",
        end_date="2020-09-01",
        position_size_method=PositionSizeMethod.FIXED_DOLLAR,
        position_size_value=10_000.0,
    )
    result = BacktestEngine(loader, MomentumStrategy(10, 30), config).run()
    price_data = loader.fetch("SYNTH", "2020-01-01", "2020-09-01")
    benchmark = buy_and_hold_equity(price_data, config.initial_cash)
    print_report(generate_report(result, benchmark_equity=benchmark))

    output_dir = ROOT / "docs"
    plot_equity_curve(result, benchmark_equity=benchmark, save_path=str(output_dir / "demo_equity_curve.png"))
    plot_drawdown(result.equity_curve, save_path=str(output_dir / "demo_drawdown.png"))
    plot_trades(price_data, result.trades, save_path=str(output_dir / "demo_trades.png"))
    print(f"demo charts written to {output_dir}")


if __name__ == "__main__":
    main()

