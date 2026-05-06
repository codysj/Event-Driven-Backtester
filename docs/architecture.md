# Architecture

## High-Level Architecture

Backtester has three visible layers:

- Core Python backtesting package in `backtester/`.
- FastAPI API wrapper in `backtester/api/`.
- Next.js dashboard in `frontend/`, branded in the UI as Backtest Lab.

The core package is intentionally modular. Data loading, strategies, portfolio state, metrics, research utilities, and visualization are independently testable. Engines and API services compose those modules. The frontend is an API client: it renders forms, validation, charts, and tables, but it does not reimplement backtesting logic.

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
- `frontend/app/`
  - Next.js App Router entrypoint, layout, global dark dashboard styles, and page-level state orchestration.
- `frontend/components/`
  - Backtest Lab UI components: app shell, sidebar, top bar, form, metric cards, charts, states, result tabs, and trade table.
- `frontend/lib/`
  - Frontend API client, TypeScript API types, defaults, and form validation helpers.
- `examples/`
  - Demo scripts and chart generation scripts.
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
- `buy_and_hold_equity()` creates a benchmark equity curve for comparison.
- `run_grid_search()` expands a parameter grid, runs backtests, and records errors per combination.
- FastAPI `POST /api/backtest` wraps a single-asset backtest for Backtest Lab.
- Frontend `frontend/lib/api.ts` isolates API calls from UI components.
- Frontend `frontend/lib/validation.ts` performs inline form validation before POST requests.

## Data Flow

### Single-Asset Python Backtest

1. `DataLoader` fetches and validates OHLCV data.
2. `BacktestEngine` initializes `Portfolio` and calls `strategy.precompute(data)`.
3. For each bar, engine passes full `data` plus `current_index` to `strategy.generate_signal`.
4. Engine converts signals into `Order`s.
5. `Portfolio` executes accepted orders and records equity.
6. Engine returns `BacktestResult`.
7. Metrics, charts, CLI, API, or frontend consume the result.

### Browser To API To Engine

1. Backtest Lab loads health status from `GET /health`.
2. Backtest Lab loads strategy metadata from `GET /api/strategies`; local fallback metadata keeps the form renderable if the API is offline.
3. User edits the single-asset config in the right-side form.
4. Frontend validates the request shape and strategy parameters inline.
5. Browser submits `BacktestRequest` to `POST /api/backtest`.
6. `backtester/api/services.py` builds `BacktestConfig` and the selected strategy.
7. Existing Python engine and metrics run server-side.
8. API returns:
   - Submitted config
   - Summary metrics
   - Equity series
   - Optional benchmark series
   - Drawdown series
   - Price series
   - Executed trades
9. Frontend renders KPI cards, Recharts equity/drawdown charts, result tabs, trades, metrics, and parameters.

### Multi-Asset Python Flow

1. Engine fetches each ticker independently.
2. DataFrames align on the intersection of dates available for all tickers.
3. Strategy returns ticker-to-signal mappings.
4. Orders execute in config ticker order.
5. Equity is recorded once per shared timestamp using all current prices.

Multi-asset support exists in Python. It is not currently exposed by FastAPI, CLI, or Backtest Lab.

## API Contract

FastAPI app: `backtester/api/main.py`

- `GET /health`
  - Response: `{ "status": "ok" }`.
- `GET /api/strategies`
  - Returns supported strategy ids, descriptions, and parameter metadata.
- `POST /api/backtest`
  - Request schema:
    - `ticker`
    - `start_date`
    - `end_date`
    - `strategy`
    - `initial_cash`
    - `commission_rate`
    - `slippage_bps`
    - `position_size_method`
    - `position_size_value`
    - `benchmark`
    - `parameters`
  - Response schema:
    - `config`
    - `summary`
    - `series.equity`
    - `series.benchmark`
    - `series.drawdown`
    - `series.price`
    - `trades`

The API normalizes ticker case and validates strategy parameters with Pydantic.

## Frontend Architecture

Backtest Lab uses Next.js App Router with client-side state in `frontend/app/page.tsx`.

Main component groups:

- `AppShell`, `Sidebar`, `TopBar`
  - Full-screen application frame and run context.
- `BacktestForm`
  - Controlled right-side configuration panel.
- `ResultsDashboard`
  - Run hero, KPI cards, chart stack, and tab orchestration.
- `EquityChart`, `DrawdownChart`
  - Recharts charts with dark financial styling and custom tooltips.
- `ResultsTabs`, `TradeTable`
  - Summary, trades, metrics, and parameters views.
- `EmptyState`, `LoadingSkeleton`, `ErrorState`
  - Non-happy-path dashboard states.
- `formatters`
  - Shared currency, percent, number, decimal, and date formatting.

The design system lives mostly in Tailwind classes plus `frontend/app/globals.css` CSS variables. Numeric values use a mono font stack through `font-mono-finance`.

## External Services And APIs

- yfinance is used for historical market data.
- FastAPI serves the local API.
- The Next.js frontend calls `NEXT_PUBLIC_API_URL`, defaulting to `http://localhost:8000`.
- No database, auth provider, broker API, payment system, paid data feed, or live trading integration is present.

## Configuration And Environment

- Python dependencies are in `requirements.txt` and `pyproject.toml`.
- Tests are configured in `pyproject.toml` with `testpaths = ["tests"]`.
- Mypy is configured strict for Python 3.11 in `pyproject.toml`.
- Frontend dependencies and scripts are in `frontend/package.json`.
- Frontend optional env file: `frontend/.env.local`, based on `frontend/.env.example`.
- API CORS currently allows:
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
- CI is `.github/workflows/ci.yml`; it installs Python requirements, runs `pytest`, and runs `mypy backtester`.
- Frontend build is not currently part of CI.

## Important Design Decisions

- No domain-specific backtesting or finance metrics libraries are used.
- Strategies use full DataFrame plus `current_index` for speed; look-ahead prevention is a strategy contract.
- Multi-asset backtests use inner-join date alignment for simplicity and predictable shared indexing.
- Rejected orders return `None`; rejection is normal simulation behavior.
- Cash is rounded to cents after trades; production-grade accounting would likely use `Decimal`.
- Backtest Lab is deliberately a single-asset API client even though the Python engine supports multi-asset backtests.
- Frontend validation improves UX but does not replace API/Pydantic validation.
- Backtest Lab favors the existing stack: Next.js, TypeScript, Tailwind CSS, Recharts, and small local components instead of heavy UI libraries.

## Needs Confirmation

- Whether frontend checks should be added to CI. Current CI is Python-only.
- Whether to expose multi-asset backtesting in API, CLI, and Backtest Lab.
- Whether to commit generated dashboard screenshots long-term or regenerate them on demand.
- Whether API CORS should support configurable frontend origins.
- Whether CLI should expose multi-asset backtesting.
- Whether live yfinance examples should be replaced with fully synthetic defaults for all demo paths.
- Whether frontend lint/typecheck scripts should be added.

