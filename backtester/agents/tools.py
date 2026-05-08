"""Safe workflow wrappers and deterministic result analysis."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from pydantic import ValidationError

from backtester.agents.research_state import ApprovedAction, WorkflowResultSummary, action_for_target_mode
from backtester.ai.schemas import TargetMode
from backtester.api.schemas import (
    BacktestRequest,
    BacktestResponse,
    GridSearchRequest,
    GridSearchResponse,
    WalkForwardRequest,
    WalkForwardResponse,
)
from backtester.api.services import (
    run_backtest_from_request,
    run_grid_search_from_request,
    run_walk_forward_from_request,
)


class WorkflowRunner(Protocol):
    """Callable surface for approved existing API workflows."""

    def run_backtest(self, request: BacktestRequest) -> BacktestResponse:
        """Run one existing single-asset backtest request."""

    def run_grid_search(self, request: GridSearchRequest) -> GridSearchResponse:
        """Run one existing single-asset grid-search request."""

    def run_walk_forward(self, request: WalkForwardRequest) -> WalkForwardResponse:
        """Run one existing single-asset walk-forward request."""


class ServiceWorkflowRunner:
    """Default wrapper around existing API service functions."""

    def run_backtest(self, request: BacktestRequest) -> BacktestResponse:
        return run_backtest_from_request(request)

    def run_grid_search(self, request: GridSearchRequest) -> GridSearchResponse:
        return run_grid_search_from_request(request)

    def run_walk_forward(self, request: WalkForwardRequest) -> WalkForwardResponse:
        return run_walk_forward_from_request(request)


def run_approved_workflow(
    target_mode: TargetMode,
    approved_action: ApprovedAction,
    payload: dict[str, object],
    runner: WorkflowRunner,
) -> BacktestResponse | GridSearchResponse | WalkForwardResponse:
    """Validate approval and execute exactly one existing workflow service call."""
    required_action = action_for_target_mode(target_mode)
    if required_action is None:
        msg = "Compiled target mode is not executable."
        raise ValueError(msg)
    if approved_action != required_action:
        msg = f"approved_action must be {required_action.value} for target_mode {target_mode.value}."
        raise ValueError(msg)

    if approved_action == ApprovedAction.RUN_BACKTEST:
        return runner.run_backtest(_validate_backtest_payload(payload))
    if approved_action == ApprovedAction.RUN_GRID_SEARCH:
        return runner.run_grid_search(_validate_grid_search_payload(payload))
    if approved_action == ApprovedAction.RUN_WALK_FORWARD:
        return runner.run_walk_forward(_validate_walk_forward_payload(payload))

    msg = f"Unsupported approved_action: {approved_action.value}."
    raise ValueError(msg)


def summarize_workflow_result(
    target_mode: TargetMode,
    result: BacktestResponse | GridSearchResponse | WalkForwardResponse,
) -> WorkflowResultSummary:
    """Extract an API-friendly summary from an existing workflow response."""
    if isinstance(result, BacktestResponse):
        summary = {
            "ticker": result.summary.ticker,
            "strategy_name": result.summary.strategy_name,
            "total_return": result.summary.total_return,
            "max_drawdown": result.summary.max_drawdown,
            "total_trades": result.summary.total_trades,
        }
        return WorkflowResultSummary(target_mode=target_mode, summary=summary, warnings=[])

    if isinstance(result, GridSearchResponse):
        summary = {
            "strategy_name": result.strategy_name,
            "total_combinations": result.total_combinations,
            "best_parameters": result.best_parameters,
            "failed_combinations": len(result.failed_combinations),
        }
        return WorkflowResultSummary(target_mode=target_mode, summary=summary, warnings=result.analysis.warnings)

    summary = {
        "strategy_name": result.strategy_name,
        "number_of_folds": result.summary.number_of_folds,
        "average_train_metric": result.summary.average_train_metric,
        "average_test_metric": result.summary.average_test_metric,
        "average_degradation": result.summary.average_degradation,
    }
    return WorkflowResultSummary(target_mode=target_mode, summary=summary, warnings=result.summary.warnings)


def analyze_workflow_result(result: BacktestResponse | GridSearchResponse | WalkForwardResponse) -> list[str]:
    """Return transparent heuristic notes for an existing workflow result."""
    notes: list[str] = []
    if isinstance(result, BacktestResponse):
        if result.series.benchmark:
            first = result.series.benchmark[0].value
            last = result.series.benchmark[-1].value
            if first:
                benchmark_return = last / first - 1.0
                if result.summary.total_return < benchmark_return:
                    notes.append("Strategy total return lagged the benchmark total return.")
        if result.summary.max_drawdown <= -0.30:
            notes.append("Max drawdown is high relative to the current heuristic threshold.")
        if result.summary.total_trades < 4:
            notes.append("Trade count is sparse; conclusions may be fragile.")
        if not notes:
            notes.append("No first-pass heuristic warnings were triggered.")
        return notes

    if isinstance(result, GridSearchResponse):
        if result.failed_combinations:
            notes.append(f"{len(result.failed_combinations)} grid-search combination(s) failed.")
        if result.best_row is not None:
            if result.best_row.excess_total_return is not None and result.best_row.excess_total_return < 0:
                notes.append("Best grid-search row underperformed the benchmark on total return.")
            if result.best_row.max_drawdown is not None and result.best_row.max_drawdown <= -0.30:
                notes.append("Best grid-search row has high max drawdown.")
            if result.best_row.total_trades < 4:
                notes.append("Best grid-search row has sparse trades.")
        notes.extend(result.analysis.warnings)
        if not notes:
            notes.append("Grid-search heuristics did not flag the current best row.")
        return notes

    if result.summary.average_degradation is not None and result.summary.average_degradation < 0.50:
        notes.append("Walk-forward validation shows substantial out-of-sample degradation.")
    notes.extend(result.summary.warnings)
    if not notes:
        notes.append("Walk-forward heuristics did not flag aggregate degradation.")
    return notes


def analyze_workflow_summary(workflow_result: WorkflowResultSummary) -> list[str]:
    """Return deterministic heuristic notes from serialized workflow summary state."""
    notes = list(workflow_result.warnings)
    summary = workflow_result.summary

    if workflow_result.target_mode == TargetMode.SINGLE_RUN:
        max_drawdown = summary.get("max_drawdown")
        if isinstance(max_drawdown, int | float) and float(max_drawdown) <= -0.30:
            notes.append("Max drawdown is high relative to the current heuristic threshold.")
        total_trades = summary.get("total_trades")
        if isinstance(total_trades, int | float) and int(total_trades) < 4:
            notes.append("Trade count is sparse; conclusions may be fragile.")

    if workflow_result.target_mode == TargetMode.GRID_SEARCH:
        failed = summary.get("failed_combinations")
        if isinstance(failed, int | float) and int(failed) > 0:
            notes.append(f"{int(failed)} grid-search combination(s) failed.")

    if workflow_result.target_mode == TargetMode.WALK_FORWARD:
        degradation = summary.get("average_degradation")
        if isinstance(degradation, int | float) and float(degradation) < 0.50:
            notes.append("Walk-forward validation shows substantial out-of-sample degradation.")

    if not notes:
        notes.append("No first-pass heuristic warnings were triggered.")
    return _unique_strings(notes)


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return unique


def _validate_backtest_payload(payload: dict[str, object]) -> BacktestRequest:
    try:
        return BacktestRequest.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(_payload_validation_message("backtest", exc)) from exc


def _validate_grid_search_payload(payload: dict[str, object]) -> GridSearchRequest:
    try:
        return GridSearchRequest.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(_payload_validation_message("grid-search", exc)) from exc


def _validate_walk_forward_payload(payload: dict[str, object]) -> WalkForwardRequest:
    try:
        return WalkForwardRequest.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(_payload_validation_message("walk-forward", exc)) from exc


def _payload_validation_message(workflow: str, exc: ValidationError) -> str:
    fields = sorted({_error_location(error) for error in exc.errors()})
    field_text = ", ".join(fields[:8]) if fields else "unknown"
    if len(fields) > 8:
        field_text = f"{field_text}, {len(fields) - 8} more"
    return f"Compiled payload did not match the {workflow} request schema; fields={field_text}."


def _error_location(error: Mapping[str, object]) -> str:
    location = error.get("loc")
    if isinstance(location, tuple) and location:
        return ".".join(str(item) for item in location)
    return "unknown"
