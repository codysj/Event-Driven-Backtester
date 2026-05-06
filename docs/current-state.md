# Current State

Last documentation pass: 2026-05-06.

## Implemented Functionality

- Data loading with yfinance and Parquet cache.
- Clean OHLCV validation with schema `open`, `high`, `low`, `close`, `volume`.
- Single-asset and multi-asset backtest engines.
- Strategy interfaces:
  - `Strategy`
  - `MultiAssetStrategy`
  - `SingleStrategyMultiAssetWrapper`
- Built-in strategies:
  - Momentum SMA crossover
  - Mean reversion with Bollinger-style bands
- Portfolio simulation:
  - Cash
  - Positions
  - Orders/trades
  - Commission
  - Slippage
  - Equity curve
- Position sizing:
  - Fixed quantity
  - Fixed dollar
  - All-in
  - Percent equity
  - Simplified volatility targeting
- Metrics:
  - Return metrics
  - Sharpe/Sortino
  - Max drawdown
  - Alpha/beta
  - Information ratio
  - Benchmark equity
  - Trade summaries
- Grid search for single-asset strategies.
- Matplotlib chart helpers.
- CLI:
  - `run`
  - `grid-search`
- FastAPI API:
  - `GET /health`
  - `GET /api/strategies`
  - `POST /api/backtest`
- Next.js dashboard:
  - Backtest form
  - Summary metric cards
  - Equity chart
  - Drawdown chart
  - Trade table
- Examples, benchmark scripts, tests, mypy config, and Python CI.

## Known Incomplete Areas

- Web dashboard only supports single-asset backtests.
- CLI does not expose multi-asset workflows.
- CI does not run frontend build checks.
- No frontend lint script is configured.
- No live deployment config.
- No auth, database, broker integration, or live trading.
- Benchmark docs include measured optimized synthetic numbers, but baseline speedup is not measured.

## Known Bugs Or TODOs

- `docs/benchmark_results.md` still has TODOs for pre-optimization baseline measurement and speedup comparison.
- README directory tree may display encoding artifacts (`â”œ...`) in some terminals.
- npm reported dependency audit findings during the previous frontend install; no forced upgrade was applied.

## Recent Assumptions From Repo State

- Python commands are the primary CI gate.
- Frontend is intended as a local demo surface, not a deployed product yet.
- Core tests should not depend on network access.
- yfinance-backed CLI/API/browser runs may require network or existing cache.
- Generated Python bytecode and frontend build outputs should remain untracked.

## Recommended Next Tasks

- Add frontend build to CI if Node build time is acceptable.
- Decide whether to expose multi-asset runs in API/frontend/CLI.
- Add a frontend lint/typecheck script if desired.
- Replace README tree with plain ASCII.
- Add a small screenshot workflow for Backtest Lab once the UI stabilizes.
- Review npm audit output and upgrade dependencies carefully without forcing breaking changes.

## Commands Verified During This Documentation Pass

The following commands were run:

```bash
pytest
mypy backtester
npm.cmd run build
```

Results:

- `pytest`: 98 passed.
- `mypy backtester`: success, no issues found in 30 source files.
- `npm.cmd run build` from `frontend/`: success, Next.js production build completed.

If these docs are read much later, rerun the commands before relying on the status.
