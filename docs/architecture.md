# Architecture

## High-Level Architecture

Backtester has three visible layers:

- Core Python backtesting package in `backtester/`
- FastAPI wrapper in `backtester/api/`
- Next.js dashboard in `frontend/`

The core package is intentionally modular. Data loading, strategies, portfolio state, metrics, research utilities, and visualization are independently testable. Engines and API services compose those pieces.

## Main Directories

- `backtester/data/`
  - Fetches OHLCV data with yfinance, cleans it, validates schema, and caches Parquet files under `~/.backtester/cache/`.
- `backtester/strategy/`
  - Defines `Strategy`, `MultiAssetStrategy`, `Signal`, built-in momentum and mean-reversion strategies, and a wrapper for applying one single-asset strategy across multiple assets.
- `backtester/portfolio/`
  - Defines `Order`, `Trade`, `Position`, and `Portfolio`. Tracks cash, positions, trade history, and equity curve.
- `backtester/engine/`
  - Contains single-asset and multi-asset engines, immutable configs, result dataclasses, and shared position sizing logic.
- `backtester/metrics/`
  - Computes returns, drawdowns, Sharpe/Sortino, alpha/beta, information ratio, profit factor, benchmark equity, and trade-level summaries.
- `backtester/research/`
  - Runs parameter grid searches and returns sorted `pandas.DataFrame` results.
- `backtester/viz/`
  - Matplotlib chart helpers for equity, drawdown, trades, and strategy comparison.
- `backtester/api/`
  - FastAPI routes, Pydantic schemas, and service conversion between engine objects and JSON responses.
- `frontend/`
  - Next.js App Router frontend with TypeScript, Tailwind CSS, and Recharts.
- `examples/`
  - Synthetic demos and chart generation scripts.
- `benchmarks/`
  - Synthetic benchmark and cProfile scripts.
- `tests/`
  - Unit and smoke tests using deterministic synthetic data where possible.

## Key Components

- `DataLoader.fetch(ticker, start, end)` returns a cleaned OHLCV `DataFrame` with lowercase columns and `DatetimeIndex` named `date`.
- `BacktestEngine.run()` runs one ticker with a `Strategy`.
- `MultiAssetBacktestEngine.run()` runs multiple tickers with a `MultiAssetStrategy`.
- `Portfolio.execute_order()` applies slippage/commission and mutates cash/positions on accepted trades.
- `generate_report()` computes primary performance metrics and optional benchmark comparison keys.
- `run_grid_search()` expands a parameter grid, runs backtests, and records errors per combination.
- FastAPI `POST /api/backtest` wraps a single-asset backtest for the web dashboard.

## Data Flow

Single-asset backtest:

1. `DataLoader` fetches and validates OHLCV data.
2. `BacktestEngine` initializes `Portfolio` and calls `strategy.precompute(data)`.
3. For each bar, engine passes full `data` plus `current_index` to `strategy.generate_signal`.
4. Engine converts signals into `Order`s.
5. `Portfolio` executes accepted orders and records equity.
6. Engine returns `BacktestResult`.
7. Metrics, charts, CLI, API, or frontend consume the result.

API/frontend flow:

1. Browser submits a `BacktestRequest` to FastAPI.
2. `backtester/api/services.py` builds `BacktestConfig` and strategy.
3. Existing engine and metrics run server-side.
4. API returns JSON series, summary metrics, and trades.
5. Frontend renders metric cards, Recharts equity/drawdown charts, and a trade table.

Multi-asset flow:

1. Engine fetches each ticker independently.
2. DataFrames align on the intersection of dates.
3. Strategy returns ticker-to-signal mappings.
4. Orders execute in config ticker order.
5. Equity is recorded once per shared timestamp using all current prices.

## External Services And APIs

- yfinance is used for historical market data.
- FastAPI serves the local API.
- The Next.js frontend calls `NEXT_PUBLIC_API_URL`, defaulting to `http://localhost:8000`.
- No database, auth provider, broker API, payment system, or live trading integration is present.

## Configuration And Environment

- Python dependencies are in `requirements.txt` and `pyproject.toml`.
- Tests are configured in `pyproject.toml` with `testpaths = ["tests"]`.
- Mypy is configured strict for Python 3.11 in `pyproject.toml`.
- Frontend dependencies and scripts are in `frontend/package.json`.
- Frontend optional env file: `frontend/.env.local`, based on `frontend/.env.example`.
- CI is `.github/workflows/ci.yml`; it installs Python requirements, runs `pytest`, and runs `mypy backtester`.

## Important Design Decisions

- No domain-specific backtesting or finance metrics libraries are used.
- Strategies use full DataFrame plus `current_index` for speed; look-ahead prevention is a strategy contract.
- Multi-asset backtests use inner-join date alignment for simplicity and predictable shared indexing.
- Rejected orders return `None`; rejection is normal simulation behavior.
- Cash is rounded to cents after trades; production-grade accounting would likely use `Decimal`.
- The web dashboard is deliberately single-asset v1 even though Python supports multi-asset backtests.

## Needs Confirmation

- Whether frontend checks should be added to CI. Current CI is Python-only.
- Whether to commit generated docs PNGs long-term or regenerate them on demand.
- Whether the README architecture tree should be re-rendered with plain ASCII; current output shows encoding artifacts in some terminals.
- Whether CLI should expose multi-asset backtesting.
- Whether live yfinance examples should be replaced with fully synthetic defaults for all demo paths.

