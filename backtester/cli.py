"""Command-line interface for Backtester."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from backtester.data.loader import DataLoader
from backtester.engine import BacktestConfig, BacktestEngine, PositionSizeMethod
from backtester.metrics import buy_and_hold_equity, generate_report, print_report
from backtester.research import run_grid_search
from backtester.strategy import MeanReversionStrategy, MomentumStrategy, Strategy
from backtester.viz import plot_drawdown, plot_equity_curve, plot_trades


def parse_int_list(value: str) -> list[int]:
    """Parse comma-separated integers from CLI input."""
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="backtester", description="Run Backtester workflows.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run one backtest.")
    run_parser.add_argument("--ticker", required=True)
    run_parser.add_argument("--start", required=True)
    run_parser.add_argument("--end", required=True)
    run_parser.add_argument("--strategy", choices=["momentum", "mean-reversion"], default="momentum")
    run_parser.add_argument("--initial-cash", type=float, default=100_000.0)
    run_parser.add_argument("--commission-rate", type=float, default=0.001)
    run_parser.add_argument("--slippage-bps", type=float, default=5.0)
    run_parser.add_argument("--position-size-method", choices=[method.name for method in PositionSizeMethod], default="FIXED_DOLLAR")
    run_parser.add_argument("--position-size-value", type=float, default=10_000.0)
    run_parser.add_argument("--fast-window", type=int, default=10)
    run_parser.add_argument("--slow-window", type=int, default=50)
    run_parser.add_argument("--window", type=int, default=20)
    run_parser.add_argument("--num-std", type=float, default=2.0)
    run_parser.add_argument("--benchmark", action="store_true")
    run_parser.add_argument("--save-charts", action="store_true")
    run_parser.add_argument("--output-dir", default="outputs")

    grid_parser = subparsers.add_parser("grid-search", help="Run a momentum parameter grid search.")
    grid_parser.add_argument("--ticker", required=True)
    grid_parser.add_argument("--start", required=True)
    grid_parser.add_argument("--end", required=True)
    grid_parser.add_argument("--strategy", choices=["momentum"], default="momentum")
    grid_parser.add_argument("--fast-windows", default="5,10")
    grid_parser.add_argument("--slow-windows", default="30,50")
    grid_parser.add_argument("--sort-by", default="sharpe_ratio")
    grid_parser.add_argument("--initial-cash", type=float, default=100_000.0)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            _run_backtest(args)
        elif args.command == "grid-search":
            _run_grid_search(args)
        else:
            parser.error("Unknown command.")
    except Exception as exc:  # noqa: BLE001 - CLI should show readable errors.
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def _run_backtest(args: argparse.Namespace) -> None:
    loader = DataLoader()
    config = BacktestConfig(
        ticker=args.ticker,
        start_date=args.start,
        end_date=args.end,
        initial_cash=args.initial_cash,
        commission_rate=args.commission_rate,
        slippage_bps=args.slippage_bps,
        position_size_method=PositionSizeMethod[args.position_size_method],
        position_size_value=args.position_size_value,
    )
    strategy = _build_strategy(args)
    result = BacktestEngine(loader=loader, strategy=strategy, config=config).run()
    benchmark_equity = None
    price_data = None
    if args.benchmark or args.save_charts:
        price_data = loader.fetch(config.ticker, config.start_date, config.end_date)
    if args.benchmark and price_data is not None:
        benchmark_equity = buy_and_hold_equity(price_data, config.initial_cash)

    print_report(generate_report(result, benchmark_equity=benchmark_equity))
    if args.save_charts and price_data is not None:
        output_dir = Path(args.output_dir)
        plot_equity_curve(result, benchmark_equity=benchmark_equity, save_path=str(output_dir / "equity_curve.png"))
        plot_drawdown(result.equity_curve, save_path=str(output_dir / "drawdown.png"))
        plot_trades(price_data, result.trades, save_path=str(output_dir / "trades.png"))
        print(f"charts saved to {output_dir}")


def _run_grid_search(args: argparse.Namespace) -> None:
    config = BacktestConfig(
        ticker=args.ticker,
        start_date=args.start,
        end_date=args.end,
        initial_cash=args.initial_cash,
    )
    results = run_grid_search(
        loader=DataLoader(),
        strategy_factory=MomentumStrategy,
        param_grid={
            "fast_window": parse_int_list(args.fast_windows),
            "slow_window": parse_int_list(args.slow_windows),
        },
        config=config,
        sort_by=args.sort_by,
    )
    print(results.to_string(index=False))


def _build_strategy(args: argparse.Namespace) -> Strategy:
    if args.strategy == "momentum":
        return MomentumStrategy(fast_window=args.fast_window, slow_window=args.slow_window)
    return MeanReversionStrategy(window=args.window, num_std=args.num_std)


if __name__ == "__main__":
    raise SystemExit(main())
