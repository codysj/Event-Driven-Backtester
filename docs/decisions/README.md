# Architecture Decision Records

This directory is for short Architecture Decision Records (ADRs): durable notes explaining important technical choices and their tradeoffs.

Use ADRs when a decision affects architecture, public APIs, dependencies, data flow, performance, or long-term maintenance.

## Naming

Use:

```text
YYYY-MM-DD-short-title.md
```

Example:

```text
2026-05-06-strategy-current-index-interface.md
```

## Template

```markdown
# Title

Date: YYYY-MM-DD

## Status

Proposed | Accepted | Superseded

## Context

What problem or tradeoff led to this decision?

## Decision

What did we choose?

## Consequences

What gets better, what gets worse, and what follow-up work may be needed?
```

## Suggested Initial ADR Topics

- Strategy API uses full DataFrame plus `current_index` instead of sliced historical DataFrames.
- Multi-asset engine aligns data on intersection of ticker dates.
- FastAPI plus Next.js chosen for the first visible frontend.
- Recharts chosen for v1 dashboard charts.
- No backtesting-specific third-party libraries.

## Index

- [2026-05-06 - Backtest Lab remains an API client](2026-05-06-backtest-lab-api-client.md)
- [2026-05-07 - AI strategies compile to a constrained rule DSL](2026-05-07-ai-rule-dsl-no-generated-code.md)
