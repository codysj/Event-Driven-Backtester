# Backtest Lab Frontend

Backtest Lab is the Next.js dashboard for the Backtester project. It is a local research UI for running single-asset backtests through the FastAPI API and inspecting equity, drawdown, metrics, trades, and submitted parameters.

The frontend does not implement backtesting logic. It calls the Python API and renders the returned response.

## Setup

Install dependencies:

```bash
npm install
```

Backtest Lab currently uses Next.js 15. Use a Node.js version compatible with Next's engine range: `^18.18.0`, `^19.8.0`, or `>=20.0.0`.

Run the development server:

```bash
npm run dev
```

Build for production:

```bash
npm run lint
npm run typecheck
npm run build
```

`npm run lint` uses ESLint with the Next.js core web vitals and TypeScript rules. `npm run typecheck` runs `next typegen && tsc --noEmit` so route/layout types exist before TypeScript validation. `npm run build` skips Next's internal lint hook because linting is run explicitly as a separate command.

## Dependency Security

The project pins a stable Next.js 15 release and uses an npm override for Next's nested PostCSS dependency so `npm audit` remains clean without jumping to Next 16. Do not replace this with `npm audit fix --force` unless a future audit leaves no safe non-force path.

## API Configuration

By default, the frontend calls:

```text
http://localhost:8000
```

Override this with `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start the API from the repo root:

```bash
python -m uvicorn backtester.api.main:app --reload
```

The API currently allows browser requests from `http://localhost:3000` and `http://127.0.0.1:3000`.

To use another local frontend port, set `BACKTESTER_CORS_ORIGINS` before starting the backend:

```bash
BACKTESTER_CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

## UI Structure

- `app/page.tsx`
  - Owns dashboard state, API health/strategy loading, request validation, and backtest submission.
- `app/globals.css`
  - Dark dashboard color variables and shared font stacks.
- `components/AppShell.tsx`
  - Full-screen shell with sidebar, top bar, main workspace, and config panel slot.
- `components/Sidebar.tsx`
  - Product identity, navigation, and built-from-scratch badge.
- `components/TopBar.tsx`
  - Current run context, API status, reset/default controls, docs/GitHub links.
- `components/BacktestForm.tsx`
  - Controlled single-asset backtest form with inline validation display.
- `components/ResultsDashboard.tsx`
  - Run hero, status, KPI cards, charts, and result tabs.
- `components/EquityChart.tsx`
  - Recharts equity curve with optional benchmark series.
- `components/DrawdownChart.tsx`
  - Recharts drawdown chart with percent axis.
- `components/ResultsTabs.tsx`
  - Summary, Trades, Metrics, and Parameters tabs.
- `components/TradeTable.tsx`
  - Executed trades table.
- `components/EmptyState.tsx`, `ErrorState.tsx`, `LoadingSkeleton.tsx`
  - Non-happy-path states.
- `components/formatters.ts`
  - Shared formatting helpers.
- `lib/api.ts`
  - API client for `GET /health`, `GET /api/strategies`, and `POST /api/backtest`.
- `lib/types.ts`
  - TypeScript request/response shapes matching the FastAPI schema.
- `lib/defaults.ts`
  - Default AAPL Momentum SMA request and fallback strategy metadata.
- `lib/validation.ts`
  - Client-side validation for form UX.

## API Assumptions

Backtest Lab assumes these API endpoints exist:

- `GET /health`
- `GET /api/strategies`
- `POST /api/backtest`

`POST /api/backtest` is single-asset. It returns submitted config, summary metrics, equity/benchmark/drawdown/price series, and trades. Multi-asset runs are supported in Python but not currently exposed to this frontend.
