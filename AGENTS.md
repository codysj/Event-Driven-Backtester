# AGENTS.md

Durable instructions for Codex and other coding agents working in this repo.

## Project Snapshot

- Backtester is a Python 3.11+ event-driven strategy backtesting engine with a FastAPI wrapper and a Next.js dashboard.
- Core Python package is in `backtester/`; frontend source is isolated in `frontend/`.
- The engine supports single-asset and multi-asset backtests, pluggable strategies, portfolio simulation, metrics, grid search, charts, CLI, and API responses.
- The project intentionally avoids backtesting-specific libraries such as backtrader, zipline, quantstats, and empyrical.
- Core tests should remain deterministic and should not depend on live yfinance/network calls.

## Commands

Python setup:

```bash
python -m pip install -r requirements.txt
```

Python validation:

```bash
pytest
mypy backtester
pytest --cov=backtester
```

API:

```bash
python -m uvicorn backtester.api.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
npm run build
```

CLI/examples:

```bash
python -m backtester.cli --help
python examples/run_demo.py
python examples/grid_search_demo.py
python examples/multi_asset_demo.py
```

## Conventions

- Keep architecture boundaries clean: `data`, `strategy`, `portfolio`, `metrics`, and `viz` should stay independently testable; `engine` and `api` compose modules.
- Preserve existing public APIs unless the user explicitly asks for a breaking change.
- Maintain strict typing for public Python functions/classes; `mypy backtester` should pass.
- Use synthetic data in tests unless testing the data loader itself with mocked yfinance.
- Frontend business logic should call the API, not reimplement backtesting logic.
- Avoid unnecessary dependencies and heavy UI libraries; prefer the current stack unless there is a clear reason.
- Do not rewrite large areas opportunistically; make small, well-scoped changes.

## Testing Expectations

- Add/update tests for behavior changes.
- For API tests, use FastAPI `TestClient` and monkeypatch service calls when avoiding network/data dependencies.
- For frontend changes, run `npm run build`; there is currently no configured frontend lint script.
- If a command fails because dependencies or network are unavailable, document that in the handoff instead of hiding it.

## Where To Look

- `README.md` for user-facing overview and run commands.
- `docs/architecture.md` for module map and data flow.
- `docs/current-state.md` for current implementation state and verified commands.
- `docs/tasks.md` for lightweight task tracking.
- `docs/decisions/README.md` for ADR guidance.

## Common Pitfalls

- Stage 7 strategy API uses full DataFrames plus `current_index`; strategies must not read rows after `current_index`.
- Multi-asset engine aligns tickers on the intersection of available dates and processes signals in config ticker order.
- The web dashboard currently exposes single-asset backtests only; multi-asset remains Python-side.
- yfinance calls may require network unless data is cached.
- Generated files such as `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `frontend/node_modules/`, and `frontend/.next/` should not be committed.

## Handoff

At the end of a session, report:

- Files changed.
- Commands run and results.
- Tests or builds not run, with reasons.
- Any assumptions, known limitations, or follow-up tasks added to `docs/tasks.md`.

