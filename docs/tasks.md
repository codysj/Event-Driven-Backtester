# Tasks

## Now

- No active Now tasks. The previous Now batch was completed on 2026-05-06:
  - Frontend lint, typecheck, audit, and build were added to CI.
  - Frontend lint and typecheck scripts were added.
  - The frontend dependency audit remained clean with the existing PostCSS override.
  - Dashboard screenshots are regenerated on demand unless a future portfolio asset is intentionally committed.
  - API CORS origins can be configured with `BACKTESTER_CORS_ORIGINS`.

## Next

- Expose multi-asset backtesting through FastAPI if the dashboard roadmap needs it.
- Add multi-asset controls/results to Backtest Lab only after the API contract exists.
- Add CLI support for multi-asset backtests.
- Add API tests for service conversion with fake loader/service injection to avoid network/data dependencies.
- Add a small screenshot or short GIF asset for the remodeled Backtest Lab if a committed portfolio asset is desired.
- Measure a pre-optimization benchmark baseline and update `docs/benchmark_results.md`.

## Later

- Add richer chart interactions or a more finance-specific charting library if Recharts becomes limiting.
- Add optional export of reports/trades to CSV.
- Add more strategy examples.
- Add benchmark history from a pre-optimization baseline commit.
- Add a public deployment guide if the project moves beyond local demo use.

## Questions / Needs Owner Input

- Should Backtest Lab stay single-asset for portfolio demo clarity, or should multi-asset be prioritized next?
- Should CI run Node installation/build on every push?
- Should examples default entirely to synthetic data to avoid network surprises?
- Should generated docs PNGs and Backtest Lab screenshots be tracked in Git?
