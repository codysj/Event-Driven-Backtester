# Current State

Last documentation pass: 2026-05-07.

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
- Grid search for single-asset strategies, including API/service conversion, failed-combination preservation, heatmap-ready response data, and robustness warnings.
- Walk-forward validation for single-asset strategies through FastAPI and Backtest Lab.
- Richer risk analytics:
  - rolling Sharpe
  - rolling volatility
  - rolling drawdown
  - drawdown duration
  - best/worst day
  - monthly returns
  - VaR/CVaR
- Matplotlib chart helpers.
- CLI:
  - `run`
  - `grid-search`
- FastAPI API:
  - `GET /health`
  - `GET /api/strategies`
  - `POST /api/ai/strategy-draft`
  - `POST /api/backtest`
  - `POST /api/grid-search`
  - `POST /api/walk-forward`
  - Configurable CORS origins through `BACKTESTER_CORS_ORIGINS`
- AI Strategy Builder backend foundation:
  - `backtester/ai/` package with strict Pydantic draft schemas.
  - Future-facing prompt template that requires structured JSON and forbids executable code.
  - `LLMProvider` protocol and deterministic `FakeStrategyDraftProvider`.
  - Semantic draft validator for dates, supported strategies, windows, unsupported concepts, and raw-code field rejection.
  - Placeholder compilers for future conversion into existing API request objects.
  - API endpoint returns draft status, warnings, unsupported items, and validation errors without calling a real LLM.
- Backtest Lab frontend:
  - Next.js 15 App Router, TypeScript, Tailwind CSS, Recharts.
  - Full-screen dark finance dashboard shell.
  - Sidebar, top run-context header, and sticky right configuration panel.
  - Mode switcher for Single Run, Grid Search, and Walk-Forward workflows.
  - Single-asset backtest form with inline validation.
  - Grid-search form with strategy parameter ranges, optimization metric, benchmark toggle, and top-N control.
  - Grid-search leaderboard, best-row summary, robustness warnings, failed-combination display, two-parameter heatmap, CSV/config export, and selected-row handoff into a single run.
  - Walk-forward form with train/test/step windows and strategy parameter grids.
  - Walk-forward fold table, train/test metric comparison, degradation ratios, aggregate warnings, and parameter stability.
  - API health indicator and strategy metadata loading.
  - Empty, loading, and error states.
  - KPI cards.
  - Equity chart with optional buy-and-hold benchmark.
  - Drawdown chart.
  - Summary, Trades, Metrics, and Parameters tabs.
  - Risk tab and frontend exports for trades CSV, metrics JSON, config JSON, and grid-search CSV.
  - Reproducibility view for submitted config and strategy parameters.
- Examples, benchmark scripts, tests, mypy config, Python CI, and frontend CI checks.

## Known Incomplete Areas

- Backtest Lab research workflows remain single-asset only.
- AI Strategy Builder is backend-only and fake-provider-only. It does not call a real LLM, compile drafts into runs, execute generated code, or modify the frontend.
- CLI does not expose multi-asset workflows.
- Walk-forward is table-first; richer charts can be added later.
- No live deployment config.
- No auth, database, broker integration, paid data feed, or live trading.
- Benchmark docs include measured optimized synthetic numbers, but baseline speedup is not measured.
- No committed Backtest Lab screenshot or GIF asset; dashboard screenshots are regenerated on demand unless a future portfolio asset is intentionally committed.
- Frontend package uses an npm override for Next's nested PostCSS dependency until a stable Next release no longer needs it.

## Known Bugs Or TODOs

- `docs/benchmark_results.md` still has TODOs for pre-optimization baseline measurement and speedup comparison.
- No committed Backtest Lab screenshot/GIF asset yet; screenshot regeneration workflow is documented.

## Recent Assumptions From Repo State

- Python and frontend commands are both CI gates.
- Frontend is intended as a local portfolio/demo surface, not a deployed product yet.
- Frontend business logic should remain an API client and should not reimplement backtesting logic.
- Backtest Lab should use a Node.js runtime compatible with Next's engine range: `^18.18.0`, `^19.8.0`, or `>=20.0.0`.
- Core tests should remain deterministic and avoid live yfinance/network calls unless explicitly testing mocked loader behavior.
- yfinance-backed CLI/API/browser runs may require network or existing cache.
- Generated Python bytecode, pytest/mypy caches, frontend build output, and `node_modules` should remain untracked.

## Recommended Next Tasks

- Decide whether to expose multi-asset runs through FastAPI, CLI, and Backtest Lab.
- Add richer walk-forward visuals if the table-first workflow needs more portfolio polish.
- Add a small screenshot workflow and committed dashboard screenshot once the UI stabilizes.
- Measure a pre-optimization baseline for `docs/benchmark_results.md`.
- Keep the frontend dependency audit clean during future upgrades.
- Compile reviewed AI drafts into existing backtest, grid-search, and walk-forward request schemas.
- Add Backtest Lab UI for inspecting and editing AI strategy drafts after the backend compile contract exists.
- Add a real provider behind the `LLMProvider` protocol with deterministic tests and no API keys committed.
- Define a small rule DSL or typed strategy intent format before supporting strategies beyond momentum and mean reversion.

## Commands Verified During This Documentation Pass

```bash
python -m pytest
python -m mypy backtester
cd frontend && npm install
cd frontend && npm audit
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run build
```

Recent documented results:

- `python -m pytest`: not run successfully. PowerShell returned `python : The term 'python' is not recognized as the name of a cmdlet, function, script file, or operable program.`
- `python -m mypy backtester`: not run successfully. PowerShell returned `python : The term 'python' is not recognized as the name of a cmdlet, function, script file, or operable program.`
- `python -m pytest --cov=backtester`: not run successfully for the same reason; no Python launcher or local `venv` was available in this workspace.
- `cmd /c npm run lint` from `frontend/`: success.
- `cmd /c npm run typecheck` from `frontend/`: success. `next typegen` generated route types and `tsc --noEmit` passed.
- `cmd /c npm run build` from `frontend/`: success. Next.js 15.5.15 production build compiled successfully and generated 4 static pages.
- `cmd /c npm audit` from `frontend/`: success after rerunning outside the sandbox to allow registry access. `found 0 vulnerabilities`.
- `cmd /c npm install next@15.5.15 postcss@^8.5.10` from `frontend/`: success. Upgraded Next and PostCSS without `npm audit fix --force`.
- `cmd /c npm install` from `frontend/`: success. Refreshed install state after adding the scoped PostCSS override.
- `cmd /c npm update postcss` from `frontend/`: success. Applied the override so Next's nested PostCSS resolved to 8.5.10.
- `cmd /c npm install --save-dev eslint eslint-config-next @eslint/eslintrc` from `frontend/`: success. Added frontend lint tooling; `npm audit` reported 0 vulnerabilities.
- `cmd /c npm install --save-dev eslint@^8.57.1` from `frontend/`: success. Pinned ESLint to a version compatible with `eslint-config-next`.
- `cmd /c npm install --save-dev eslint-config-next@15.5.15` from `frontend/`: success. Aligned the lint config package with Next.js 15.5.15.
- `cmd /c npm ci` from `frontend/`: not run successfully in the local Windows workspace. npm returned `EPERM: operation not permitted, unlink ...next-swc.win32-x64-msvc.node`; this appears to be a local native-binary file lock/permission issue, not a lockfile consistency issue.
- `cmd /c npm install` from `frontend/`: success after rerunning outside the sandbox to recover from the local npm cache/node_modules EPERM error.
- `cmd /c npm audit` from `frontend/`: success. `found 0 vulnerabilities`.
- `cmd /c npm run lint` from `frontend/`: success.
- `cmd /c npm run typecheck` from `frontend/`: success. `next typegen` generated route types and `tsc --noEmit` passed.
- `cmd /c npm run build` from `frontend/`: success. Next.js 15.5.15 production build compiled successfully, skipped internal linting because lint is run separately, checked validity of types, generated 4 static pages, and reported `/` at 117 kB with 219 kB first-load JS.

If these docs are read later, rerun the commands before relying on the status.
