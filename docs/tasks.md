# Tasks

## Now

- Decide whether frontend build should be added to `.github/workflows/ci.yml`.
- Fix README architecture tree encoding to plain ASCII.
- Review npm audit findings from the frontend dependency tree.
- Decide whether generated chart PNGs in `docs/` should be committed or regenerated on demand.

## Next

- Expose multi-asset backtesting through FastAPI.
- Add multi-asset controls/results to Backtest Lab.
- Add CLI support for multi-asset backtests.
- Add a frontend lint script and decide on ESLint rules.
- Add API tests for real service conversion with a fake loader/service injection pattern.
- Add screenshot or short GIF assets for the web dashboard.

## Later

- Add richer chart interactions or a more finance-specific charting library if Recharts becomes limiting.
- Add more strategy examples.
- Add benchmark history from a pre-optimization baseline commit.
- Add optional export of reports/trades to CSV.
- Add a public deployment guide if the project moves beyond local demo use.

## Questions / Needs Owner Input

- Should Backtest Lab stay single-asset for portfolio demo clarity, or should multi-asset be prioritized?
- Should CI run Node installation/build on every push?
- Should npm audit warnings be addressed immediately or deferred until dependency versions settle?
- Should examples default entirely to synthetic data to avoid network surprises?
- Should generated docs PNGs be tracked in Git?

