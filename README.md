# Backtester

Backtester is an event-driven Python backtesting engine for running pluggable trading strategies over OHLCV data.

## Built From Scratch

No backtesting libraries are used. The data loading, strategy interface, portfolio simulation, performance metrics, visualization, and engine loop are implemented from first principles with general-purpose Python tools.

## Features

- Event-driven bar-by-bar simulation
- Pluggable `Strategy` abstract base class
- Historical OHLCV loading with yfinance and Parquet caching
- Portfolio simulation with per-share commission and basis-point slippage
- Performance metrics from scratch
- Static matplotlib visualization charts
- Benchmark and cProfile scripts
- pytest, mypy, and GitHub Actions CI

## Architecture

```text
backtester/
├── backtester/
│   ├── data/
│   ├── strategy/
│   ├── portfolio/
│   ├── engine/
│   ├── metrics/
│   └── viz/
├── benchmarks/
├── docs/
├── examples/
└── tests/
```

The data, strategy, portfolio, metrics, and visualization modules stay independent. The engine is the composition layer that wires a `DataLoader`, `Strategy`, `Portfolio`, and `BacktestConfig` together.

## Quick Start

```python
from backtester.data.loader import DataLoader
from backtester.engine import BacktestConfig, BacktestEngine
from backtester.metrics import generate_report, print_report
from backtester.strategy import MomentumStrategy

config = BacktestConfig(ticker="AAPL", start_date="2018-01-01", end_date="2023-12-31")
engine = BacktestEngine(
    loader=DataLoader(),
    strategy=MomentumStrategy(fast_window=10, slow_window=50),
    config=config,
)

result = engine.run()
print_report(generate_report(result))
```

## Strategies

`MomentumStrategy` uses fast and slow simple moving averages on close prices. It buys when the fast SMA crosses above the slow SMA and sells when it crosses below.

`MeanReversionStrategy` uses Bollinger-style bands around a rolling mean. It buys when price is at or below the lower band and sells when price is at or above the upper band.

Both strategies implement the same `Strategy` interface and are interchangeable in the engine.

## Performance Metrics

Implemented metrics:

- Total return
- Annualized return
- Sharpe ratio
- Sortino ratio
- Max drawdown
- Win rate
- Profit factor

## Visualization

Chart helpers live in `backtester.viz`:

- `plot_equity_curve`
- `plot_drawdown`
- `plot_trades`
- `plot_strategy_comparison`

Generate example PNGs with:

```bash
python examples/generate_charts.py
```

If generated, example charts are written to `docs/equity_curve.png`, `docs/drawdown.png`, `docs/trades.png`, and `docs/comparison.png`.

![Equity curve](docs/equity_curve.png)
![Drawdown](docs/drawdown.png)
![Trades](docs/trades.png)
![Strategy comparison](docs/comparison.png)

## Performance Optimization

The Stage 4 engine prevented look-ahead bias structurally by slicing `data.iloc[:i + 1]` before each strategy call. Stage 7 removes that expensive per-bar DataFrame copy.

The optimized interface passes the full DataFrame plus `current_index`:

```python
strategy.generate_signal(data, current_index=i)
```

This improves speed by allowing:

- Precomputed rolling indicators
- Full-DataFrame strategy access without repeated slicing
- NumPy close-price access in the engine hot loop

The tradeoff is important: look-ahead prevention is now a strategy contract. Strategies must never read rows after `current_index`. Built-in strategies are tested against slow sliced-reference implementations to guard this behavior.

Benchmark instructions and current result table live in [docs/benchmark_results.md](docs/benchmark_results.md). No fake benchmark numbers are included.

## Testing

```bash
pytest
pytest --cov=backtester
mypy backtester
```

## Examples

```bash
python examples/simple_momentum.py
python examples/compare_strategies.py
python examples/generate_charts.py
```

## Tech Stack

- Python 3.11+
- pandas
- numpy
- yfinance
- pyarrow
- matplotlib
- pytest
- mypy
