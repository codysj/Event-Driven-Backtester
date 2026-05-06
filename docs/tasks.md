# Tasks

## Now

- Add frontend build to `.github/workflows/ci.yml` if Node build time is acceptable.
- Add a frontend lint script and decide on ESLint rules.
- Add an explicit frontend typecheck script if useful beyond `next build`.
- Review npm audit findings from the frontend dependency tree.
- Decide whether generated chart/dashboard screenshots in `docs/` should be committed or regenerated on demand.
- Consider making API CORS origins configurable for non-3000 frontend dev ports.

## Next

- Expose multi-asset backtesting through FastAPI if the dashboard roadmap needs it.
- Add multi-asset controls/results to Backtest Lab only after the API contract exists.
- Add CLI support for multi-asset backtests.
- Add API tests for service conversion with fake loader/service injection to avoid network/data dependencies.
- Add a small screenshot or short GIF asset for the remodeled Backtest Lab.
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
- Should npm audit warnings be addressed immediately or deferred until dependency versions settle?
- Should examples default entirely to synthetic data to avoid network surprises?
- Should generated docs PNGs and Backtest Lab screenshots be tracked in Git?

