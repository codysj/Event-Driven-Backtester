# Backtest Lab Remains An API Client

Date: 2026-05-06

## Status

Accepted

## Context

The frontend remodel turned Backtest Lab from a bare demo into a polished research dashboard with richer configuration, charts, states, and result tabs. That created a tempting place to add frontend-side finance calculations for convenience.

Backtester already has a Python engine, portfolio simulator, metrics package, and FastAPI layer. Duplicating that logic in TypeScript would create two sources of truth for backtest behavior and make future maintenance harder.

## Decision

Backtest Lab remains an API client and presentation layer. It may validate forms, format numbers, manage UI state, and render charts/tables, but it must submit backtest requests to FastAPI and render the API response. Backtesting, portfolio accounting, benchmark generation, and performance metrics stay server-side in the Python package.

## Consequences

- The UI stays consistent with the Python engine and metrics.
- Backend/API tests remain the primary correctness layer for simulations.
- Frontend code stays focused on UX, visualization, and API integration.
- The dashboard requires the local FastAPI server for real backtest runs.
- New frontend analytics views should prefer API additions over TypeScript reimplementation.

