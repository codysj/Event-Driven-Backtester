# Tasks

## Now

- AI Strategy Builder backend skeleton added:
  - `backtester/ai/` schemas, prompt template, provider abstraction/factory, deterministic fake provider, optional OpenAI-compatible provider, validator, and compilers.
  - OpenRouter is available as a first-class backend provider with default model `tencent/hy3-preview:free`, server-side bearer auth, chat-completions requests, and optional app attribution headers.
  - `POST /api/ai/strategy-draft` returns inert, validated draft JSON. Fake remains the default provider; real providers are server-side opt-in through env vars.
  - `POST /api/ai/compile` compiles reviewed drafts into existing Backtest, Grid Search, and Walk-Forward request payloads.
  - Backtest Lab AI Builder UI now drafts from prompts, previews assumptions/warnings/unsupported items, compiles drafts, and loads compiled configs into existing workflow forms.
  - Constrained rule-based strategy DSL added for AI Builder single-run handoff: close, SMA, prior rolling high/low, Bollinger bands, and simple comparison/cross operators.
  - No generated Python execution, persistence, broker integration, live trading, frontend API-key handling, or committed secrets.

The latest research-workstation batch added:
  - `POST /api/grid-search` with leaderboard rows, failed-combination preservation, heatmap data, and robustness warnings.
  - `POST /api/walk-forward` with train/test folds, selected parameters, degradation ratios, aggregate warnings, and parameter stability.
  - Backtest Lab mode switcher for Single Run, Grid Search, and Walk-Forward workflows.
  - Richer server-side risk analytics and frontend exports.

## Next

- Expose multi-asset backtesting through FastAPI if the dashboard roadmap needs it.
- Expand the rule DSL only when there is a tested strategy intent contract for more indicators, OR composition, and research optimization.
- Add multi-asset controls/results to Backtest Lab only after the API contract exists.
- Add CLI support for multi-asset backtests.
- Add a small screenshot or short GIF asset for the remodeled Backtest Lab if a committed portfolio asset is desired.
- Add richer walk-forward charts once the table-first validation workflow has settled.
- Add backend export endpoints only if frontend-side CSV/JSON export becomes insufficient.
- Add a local Python interpreter/venv setup note or script for Windows workspaces where `python` is not on PATH.
- Measure a pre-optimization benchmark baseline and update `docs/benchmark_results.md`.
- Revisit AI Builder provider quality if OpenRouter free-model rate limits or availability become noisy during demos.
- Improve AI Builder DSL prompting with more few-shot examples for rule-based drafts.
- Evaluate stronger structured-output support for providers/models that can enforce JSON schema directly.
- Add model-specific tuning notes for OpenRouter free models and any paid models used in demos.

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
