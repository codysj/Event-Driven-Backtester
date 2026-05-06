# Backtester

Backtester is an event-driven Python backtesting engine for researching trading strategies over historical OHLCV data. It includes a FastAPI wrapper and a polished Next.js dashboard called **Backtest Lab** for running single-asset simulations from the browser.

The project is built as a portfolio-quality demonstration of backtesting architecture, API integration, and financial dashboard UX. It is a research tool only, not a brokerage app or investment advisor.

## Built From Scratch

Backtester intentionally avoids backtesting-specific libraries such as backtrader, zipline, quantstats, and empyrical. Data loading, strategy interfaces, portfolio simulation, performance metrics, benchmark comparison, visualization, and engine loops are implemented from first principles with general-purpose Python tools.

## Current Features

- Event-driven bar-by-bar simulation.
- Pluggable strategy interfaces for single-asset and multi-asset workflows.
- Built-in Momentum SMA Crossover and Mean Reversion strategies.
- Historical OHLCV loading with yfinance and Parquet caching.
- Portfolio simulation with cash, positions, trades, commissions, slippage, and equity curves.
- Position sizing methods:
  - Fixed quantity
  - Fixed dollar
  - All-in
  - Percent equity
  - Simplified volatility targeting
- Performance metrics from scratch:
  - Total and annualized return
  - Sharpe and Sortino ratios
  - Max drawdown
  - Win rate and profit factor
  - Alpha, beta, excess return, and information ratio when a benchmark is supplied
- Buy-and-hold benchmark equity generation.
- Trade-level analytics.
- Single-asset grid search.
- Matplotlib chart helpers.
- CLI commands for single-asset backtests and grid searches.
- FastAPI API for local app integration.
- Backtest Lab dashboard built with Next.js, TypeScript, Tailwind CSS, and Recharts.
- pytest and mypy validation through Python CI.

## Project Layout

```text
Backtester/
|-- backtester/
|   |-- api/
|   |-- data/
|   |-- engine/
|   |-- metrics/
|   |-- portfolio/
|   |-- research/
|   |-- strategy/
|   `-- viz/
|-- benchmarks/
|-- docs/
|-- examples/
|-- frontend/
|   |-- app/
|   |-- components/
|   `-- lib/
|-- tests/
|-- pyproject.toml
`-- requirements.txt
```

## Quick Start

Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Run Python validation:

```bash
pytest
mypy backtester
pytest --cov=backtester
```

Start the FastAPI backend:

```bash
python -m uvicorn backtester.api.main:app --reload
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend uses Next.js 15 and requires a compatible Node.js runtime (`^18.18.0`, `^19.8.0`, or `>=20.0.0`). The current local validation was run with Node 24.14.0 and npm 11.9.0.

Build the frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

`npm run lint` uses ESLint with the Next.js core web vitals and TypeScript rules. `npm run typecheck` runs `next typegen && tsc --noEmit`.

## Backtest Lab Dashboard

**Backtest Lab** is the local browser interface for single-asset research. It is designed as a compact dark-mode financial research workstation rather than a toy demo.

Current dashboard capabilities:

- Full-screen app shell with sidebar navigation, compact run context header, and sticky configuration panel.
- API health indicator based on `GET /health`.
- Strategy metadata loaded from `GET /api/strategies`, with local fallbacks for offline form rendering.
- Single-asset backtest form for:
  - Ticker
  - Start and end dates
  - Strategy selection
  - Momentum and mean-reversion parameters
  - Initial cash
  - Position sizing method and value
  - Commission
  - Slippage in basis points
  - Buy-and-hold benchmark toggle
- Inline validation for ticker, date range, cash, costs, sizing, and strategy parameters.
- Run status, loading skeletons, empty state, and actionable API/error state.
- KPI cards for total return, annualized return, Sharpe, Sortino, max drawdown, final value, total trades, and win rate.
- Equity chart with optional benchmark line.
- Drawdown chart with percent axis and negative drawdown display.
- Tabs for Summary, Trades, Metrics, and Parameters.
- Reproducibility view showing the submitted config and strategy parameters.
- Research disclaimer: not investment advice.

The frontend does not implement backtesting logic in TypeScript. It submits requests to FastAPI and renders the returned metrics, series, trades, and config.

## API

FastAPI app: `backtester/api/main.py`

Endpoints:

- `GET /health`
  - Returns API status.
- `GET /api/strategies`
  - Returns strategy ids, labels, descriptions, and parameter metadata for the frontend form.
- `POST /api/backtest`
  - Runs a single-asset backtest through the Python engine.
  - Request fields include ticker, date range, strategy, initial cash, commission, slippage, sizing method/value, benchmark toggle, and strategy parameters.
  - Response includes config, summary metrics, equity/benchmark/drawdown/price series, and executed trades.

By default, the frontend calls `http://localhost:8000`. Override this with `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

By default, the API allows browser requests from `http://localhost:3000` and `http://127.0.0.1:3000`. To use another frontend origin, set a comma-separated backend environment variable before starting FastAPI:

```bash
BACKTESTER_CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Local API + Frontend Workflow

1. Start the API from the repo root:

   ```bash
   python -m uvicorn backtester.api.main:app --reload
   ```

2. In a second terminal, start the frontend:

   ```bash
   cd frontend
   npm run dev
   ```

3. Open `http://localhost:3000`.
4. Use the default AAPL Momentum SMA setup or adjust the config.
5. Run the backtest and inspect equity, drawdown, trades, metrics, and parameters.

yfinance may require network access unless the requested data is already cached.

## Python Usage

Single-asset example:

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

Multi-asset example:

```python
from backtester.data.loader import DataLoader
from backtester.engine import MultiAssetBacktestConfig, MultiAssetBacktestEngine
from backtester.strategy import MomentumStrategy, SingleStrategyMultiAssetWrapper

config = MultiAssetBacktestConfig(
    tickers=["AAPL", "MSFT", "GOOG"],
    start_date="2020-01-01",
    end_date="2023-12-31",
)
strategy = SingleStrategyMultiAssetWrapper(lambda: MomentumStrategy(10, 50))
result = MultiAssetBacktestEngine(DataLoader(), strategy, config).run()
```

Multi-asset support is available in the Python engine. It is not currently exposed in the FastAPI endpoint, CLI, or Backtest Lab UI.

## CLI

```bash
python -m backtester.cli --help
python -m backtester.cli run --ticker AAPL --strategy momentum --start 2020-01-01 --end 2023-12-31 --benchmark
python -m backtester.cli grid-search --ticker AAPL --start 2020-01-01 --end 2023-12-31 --fast-windows 5,10 --slow-windows 30,50
```

The CLI uses live/cached `DataLoader` data. Example scripts use synthetic data where practical to avoid network surprises.

## Strategies

- `MomentumStrategy`
  - Uses fast and slow simple moving averages on close prices.
  - Buys when the fast SMA crosses above the slow SMA.
  - Sells when the fast SMA crosses below the slow SMA.
- `MeanReversionStrategy`
  - Uses Bollinger-style bands around a rolling mean.
  - Buys when price is at or below the lower band.
  - Sells when price is at or above the upper band.
- `SingleStrategyMultiAssetWrapper`
  - Applies a single-asset strategy factory across multiple tickers for Python-side multi-asset runs.

## Visualization And Screenshots

Matplotlib helpers live in `backtester/viz/`:

- `plot_equity_curve`
- `plot_drawdown`
- `plot_trades`
- `plot_strategy_comparison`

Generate example chart PNGs:

```bash
python examples/generate_charts.py
```

Backtest Lab screenshot assets are not currently committed. Regenerate dashboard screenshots on demand for portfolio materials: start the API and frontend, run the default AAPL backtest, and capture the dashboard at desktop width. Keep generated screenshots small and intentional if they are later committed.

## Testing And CI

Current CI is `.github/workflows/ci.yml` and runs on push and pull request:

- Install Python 3.11 dependencies from `requirements.txt`.
- Run `python -m pytest`.
- Run `python -m mypy backtester`.
- Install frontend dependencies with `npm ci`.
- Run `npm audit`.
- Run `npm run lint`.
- Run `npm run typecheck`.
- Run `npm run build`.

## Known Limitations

- Backtest Lab and `POST /api/backtest` currently support single-asset backtests only.
- The Python engine supports multi-asset backtests, but the API, CLI, and frontend do not expose that workflow yet.
- No authentication.
- No database or saved run persistence.
- No broker integration.
- No live trading or order placement.
- No paid data feed integration.
- yfinance-backed workflows may require network access unless data is cached.
- Benchmark documentation still lacks a measured pre-optimization baseline comparison.
- The frontend uses an npm override to keep Next's nested PostCSS dependency on a patched 8.5.x release until Next publishes a stable line that no longer needs the override.

## Tech Stack

- Python 3.11+
- pandas, numpy
- yfinance, pyarrow
- FastAPI, Pydantic, Uvicorn
- matplotlib
- pytest, pytest-cov, mypy
- Next.js App Router
- React, TypeScript
- Tailwind CSS
- Recharts
- lucide-react
