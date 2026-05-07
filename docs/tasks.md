# Tasks

## Now

- AI Strategy Builder backend skeleton added:
  - `backtester/ai/` schemas, prompt template, provider abstraction, deterministic fake provider, validator, and placeholder compilers.
  - `POST /api/ai/strategy-draft` returns inert, validated draft JSON.
  - No real LLM calls, generated Python execution, frontend UI, persistence, broker integration, or live trading.

The latest research-workstation batch added:
  - `POST /api/grid-search` with leaderboard rows, failed-combination preservation, heatmap data, and robustness warnings.
  - `POST /api/walk-forward` with train/test folds, selected parameters, degradation ratios, aggregate warnings, and parameter stability.
  - Backtest Lab mode switcher for Single Run, Grid Search, and Walk-Forward workflows.
  - Richer server-side risk analytics and frontend exports.

## Next

- Expose multi-asset backtesting through FastAPI if the dashboard roadmap needs it.
- Compile reviewed AI strategy drafts into existing Backtest, Grid Search, and Walk-Forward request models.
- Add Backtest Lab AI draft UI only after the backend compile contract exists.
- Add a real `LLMProvider` implementation with deterministic mocked tests and no committed secrets.
- Define a small typed rule DSL or strategy intent layer before expanding AI-generated strategy coverage.
- Add multi-asset controls/results to Backtest Lab only after the API contract exists.
- Add CLI support for multi-asset backtests.
- Add a small screenshot or short GIF asset for the remodeled Backtest Lab if a committed portfolio asset is desired.
- Add richer walk-forward charts once the table-first validation workflow has settled.
- Add backend export endpoints only if frontend-side CSV/JSON export becomes insufficient.
- Add a local Python interpreter/venv setup note or script for Windows workspaces where `python` is not on PATH.
- Measure a pre-optimization benchmark baseline and update `docs/benchmark_results.md`.

## Later

- Add richer chart interactions or a more finance-specific charting library if Recharts becomes limiting.
- Add more strategy examples.
- Add benchmark history from a pre-optimization baseline commit.
- Add a public deployment guide if the project moves beyond local demo use.

## Questions / Needs Owner Input

- Should Backtest Lab stay single-asset for portfolio demo clarity, or should multi-asset be prioritized next?
- Should CI run Node installation/build on every push?
- Should examples default entirely to synthetic data to avoid network surprises?
- Should generated docs PNGs and Backtest Lab screenshots be tracked in Git?
