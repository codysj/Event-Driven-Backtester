from __future__ import annotations

import json
from collections.abc import Mapping

from backtester.agents import ApprovedAction, ResearchGraphState, run_research_graph
from backtester.ai import FakeStrategyDraftProvider
from backtester.ai.schemas import StrategyDraftRequest
from backtester.api.schemas import (
    GridSearchResponse,
    GridSearchRow,
    HeatmapPoint,
    RobustnessAnalysis,
)


class CountingRunner:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def run_backtest(self, request: object) -> object:
        del request
        self.calls.append("run_backtest")
        raise AssertionError("backtest should not be called in this test")

    def run_grid_search(self, request: object) -> GridSearchResponse:
        self.calls.append("run_grid_search")
        return GridSearchResponse(
            config={"ticker": getattr(request, "ticker", "AAPL")},
            strategy_id="momentum",
            strategy_name="Momentum SMA Crossover",
            optimization_metric="sharpe_ratio",
            total_combinations=2,
            results=[
                GridSearchRow(
                    rank=1,
                    parameters={"fast_window": 10, "slow_window": 50},
                    final_value=101000.0,
                    total_return=0.01,
                    annualized_return=0.02,
                    sharpe_ratio=0.8,
                    sortino_ratio=0.9,
                    max_drawdown=-0.05,
                    information_ratio=None,
                    benchmark_total_return=0.03,
                    excess_total_return=-0.02,
                    profit_factor=1.2,
                    win_rate=0.5,
                    total_trades=2,
                )
            ],
            failed_combinations=[
                GridSearchRow(
                    rank=None,
                    parameters={"fast_window": 80, "slow_window": 50},
                    final_value=None,
                    total_return=None,
                    annualized_return=None,
                    sharpe_ratio=None,
                    sortino_ratio=None,
                    max_drawdown=None,
                    information_ratio=None,
                    benchmark_total_return=None,
                    excess_total_return=None,
                    profit_factor=None,
                    win_rate=None,
                    total_trades=0,
                    error="fast_window must be less than slow_window",
                )
            ],
            best_parameters={"fast_window": 10, "slow_window": 50},
            best_row=None,
            heatmap=[
                HeatmapPoint(
                    x_param="fast_window",
                    y_param="slow_window",
                    x=10,
                    y=50,
                    value=0.8,
                    parameters={"fast_window": 10, "slow_window": 50},
                )
            ],
            analysis=RobustnessAnalysis(
                robustness_score=70,
                warnings=["1 parameter combination(s) failed."],
                notes=["Heuristics are a research aid, not a guarantee of future performance."],
                nearby_parameter_stability=None,
                trade_count_flags=[],
                drawdown_flags=[],
                overfit_risk_flags=[],
            ),
        )

    def run_walk_forward(self, request: object) -> object:
        del request
        self.calls.append("run_walk_forward")
        raise AssertionError("walk-forward should not be called in this test")


class MalformedProvider:
    def draft_strategy(self, request: StrategyDraftRequest) -> Mapping[str, object]:
        del request
        return {
            "status": "ready",
            "strategy_kind": "momentum",
            "parameters": {"fast_window": "not numeric"},
            "secret_payload": "do not surface this",
        }


def test_graph_stops_before_execution_without_approval() -> None:
    runner = CountingRunner()
    state = ResearchGraphState(user_goal="Optimize AAPL using a 20/100 SMA crossover")

    result = run_research_graph(state, provider=FakeStrategyDraftProvider(), workflow_runner=runner)

    assert result.approval_required is True
    assert result.approved_action is None
    assert result.compile_payload is not None
    assert result.current_step.value == "await_user_approval"
    assert runner.calls == []


def test_graph_records_draft_and_compile_warnings() -> None:
    state = ResearchGraphState(user_goal="Optimize AAPL using a 20/100 SMA crossover")

    result = run_research_graph(state, provider=FakeStrategyDraftProvider(), workflow_runner=CountingRunner())

    assert "Draft only. Review before compiling or running a backtest." in result.warnings
    assert "Default date range 2020-01-01 to 2023-12-31 was inferred." in result.warnings
    assert "Default parameter grid ranges were inferred." in result.warnings


def test_graph_refuses_mismatched_approval() -> None:
    runner = CountingRunner()
    first = run_research_graph(
        ResearchGraphState(user_goal="Optimize AAPL using a 20/100 SMA crossover"),
        provider=FakeStrategyDraftProvider(),
        workflow_runner=runner,
    )
    approved = first.model_copy(update={"approved_action": ApprovedAction.RUN_BACKTEST})

    result = run_research_graph(approved, provider=FakeStrategyDraftProvider(), workflow_runner=runner)

    assert runner.calls == []
    assert result.approval_required is True
    assert any("approved_action must be run_grid_search" in error for error in result.validation_errors)


def test_graph_resumes_with_approval_and_calls_runner_once() -> None:
    runner = CountingRunner()
    first = run_research_graph(
        ResearchGraphState(user_goal="Optimize AAPL using a 20/100 SMA crossover"),
        provider=FakeStrategyDraftProvider(),
        workflow_runner=runner,
    )
    approved = first.model_copy(update={"approved_action": ApprovedAction.RUN_GRID_SEARCH})

    result = run_research_graph(approved, provider=FakeStrategyDraftProvider(), workflow_runner=runner)

    assert runner.calls == ["run_grid_search"]
    assert result.workflow_result is not None
    assert result.workflow_result.summary["failed_combinations"] == 1
    assert any("grid-search combination" in note for note in result.analysis)
    assert result.approval_required is False


def test_graph_handles_validation_failure_without_raw_provider_payload() -> None:
    result = run_research_graph(
        ResearchGraphState(user_goal="Run AAPL with momentum"),
        provider=MalformedProvider(),
        workflow_runner=CountingRunner(),
    )

    serialized = json.dumps(result.model_dump(mode="json"))
    assert result.compile_payload is None
    assert result.validation_errors
    assert "do not surface this" not in serialized
    assert result.approval_required is False


def test_graph_state_is_json_serializable() -> None:
    result = run_research_graph(
        ResearchGraphState(user_goal="Run AAPL from 2020 to 2023 using a 20/100 SMA crossover"),
        provider=FakeStrategyDraftProvider(),
        workflow_runner=CountingRunner(),
    )

    json.dumps(result.model_dump(mode="json"))
