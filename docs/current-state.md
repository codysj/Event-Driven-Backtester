# Current State

Last documentation pass: 2026-05-06.

## Implemented Functionality

- Data loading with yfinance and Parquet cache under `~/.backtester/cache/`.
- Clean OHLCV validation with schema `open`, `high`, `low`, `close`, `volume`.
- Single-asset backtest engine.
- Multi-asset backtest engine with intersection-based date alignment.
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
  - Total and annualized return
  - Sharpe/Sortino
  - Max drawdown
  - Alpha/beta
  - Excess returns
  - Information ratio
  - Benchmark equity
  - Win rate and profit factor
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
- Backtest Lab frontend:
  - Next.js App Router, TypeScript, Tailwind CSS, Recharts.
  - Full-screen dark finance dashboard shell.
  - Sidebar, top run-context header, and sticky right configuration panel.
  - Single-asset backtest form with inline validation.
  - API health indicator and strategy metadata loading.
  - Empty, loading, and error states.
  - KPI cards.
  - Equity chart with optional buy-and-hold benchmark.
  - Drawdown chart.
  - Summary, Trades, Metrics, and Parameters tabs.
  - Reproducibility view for submitted config and strategy parameters.
- Examples, benchmark scripts, tests, mypy config, and Python CI.

## Known Incomplete Areas

- Backtest Lab only supports single-asset backtests.
- FastAPI only exposes a single-asset `POST /api/backtest` endpoint.
- CLI does not expose multi-asset workflows.
- CI does not run frontend install/build checks.
- No frontend lint or standalone typecheck script is configured.
- No live deployment config.
- No auth, database, broker integration, paid data feed, or live trading.
- Benchmark docs include measured optimized synthetic numbers, but baseline speedup is not measured.
- No committed Backtest Lab screenshot or GIF asset.

## Known Bugs Or TODOs

- `docs/benchmark_results.md` still has TODOs for pre-optimization baseline measurement and speedup comparison.
- npm previously reported dependency audit findings in the frontend dependency tree; no forced upgrade was applied.
- API CORS currently allows `localhost:3000` and `127.0.0.1:3000`; using another frontend port may require API CORS adjustment for browser backtest requests.

## Recent Assumptions From Repo State

- Python commands are the primary CI gate.
- Frontend is intended as a local portfolio/demo surface, not a deployed product yet.
- Frontend business logic should remain an API client and should not reimplement backtesting logic.
- Core tests should remain deterministic and avoid live yfinance/network calls unless explicitly testing mocked loader behavior.
- yfinance-backed CLI/API/browser runs may require network or existing cache.
- Generated Python bytecode, pytest/mypy caches, frontend build output, and `node_modules` should remain untracked.

## Recommended Next Tasks

- Add frontend build to CI if Node build time is acceptable.
- Add a frontend lint and/or explicit typecheck script.
- Decide whether to expose multi-asset runs through FastAPI, CLI, and Backtest Lab.
- Add API tests around service conversion using fake loader/service injection to avoid network calls.
- Add a small screenshot workflow and committed dashboard screenshot once the UI stabilizes.
- Review npm audit findings and upgrade dependencies carefully without forcing breaking changes.
- Measure a pre-optimization baseline for `docs/benchmark_results.md`.
- Consider expanding API CORS configuration or documenting the expected frontend port more prominently.

## Commands Verified During This Documentation Pass

```bash
pytest
mypy backtester
cd frontend && npm run build
```

Results from this pass:

- `pytest`: not run successfully. PowerShell returned `pytest : The term 'pytest' is not recognized as the name of a cmdlet, function, script file, or operable program.`
- `mypy backtester`: not run successfully. PowerShell returned `mypy : The term 'mypy' is not recognized as the name of a cmdlet, function, script file, or operable program.`
- `cmd /c npm run build` from `frontend/`: success. Next.js 14.2.35 production build compiled successfully, checked validity of types, generated 4 static pages, and reported `/` at 114 kB with 202 kB first-load JS.
- `npm run lint`: not run because `frontend/package.json` does not define a `lint` script.
- `npm run typecheck`: not run because `frontend/package.json` does not define a `typecheck` script.

If these docs are read later, rerun the commands before relying on the status.
