"""Skeleton compilers from inert strategy drafts to existing API request models."""

from __future__ import annotations

from backtester.ai.schemas import StrategyDraft
from backtester.api.schemas import BacktestRequest, GridSearchRequest, WalkForwardRequest


class DraftCompileNotImplementedError(NotImplementedError):
    """Raised until draft compilation is implemented in a follow-up task."""


def compile_backtest_request(draft: StrategyDraft) -> BacktestRequest:
    """Compile a ready single-run draft into BacktestRequest in a future task."""
    del draft
    raise DraftCompileNotImplementedError("AI draft compilation to BacktestRequest is not implemented yet.")


def compile_grid_search_request(draft: StrategyDraft) -> GridSearchRequest:
    """Compile a ready grid-search draft into GridSearchRequest in a future task."""
    del draft
    raise DraftCompileNotImplementedError("AI draft compilation to GridSearchRequest is not implemented yet.")


def compile_walk_forward_request(draft: StrategyDraft) -> WalkForwardRequest:
    """Compile a ready walk-forward draft into WalkForwardRequest in a future task."""
    del draft
    raise DraftCompileNotImplementedError("AI draft compilation to WalkForwardRequest is not implemented yet.")
