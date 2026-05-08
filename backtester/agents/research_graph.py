"""LangGraph wiring for the backend Research Copilot skeleton."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, NotRequired, TypedDict

import backtester.agents.nodes as nodes
from backtester.agents.research_state import ResearchGraphState
from backtester.agents.tools import WorkflowRunner
from backtester.ai import LLMProvider


class ResearchGraphDependencyError(RuntimeError):
    """Raised when LangGraph is unavailable for research orchestration."""


class _GraphState(TypedDict, total=False):
    session_id: str
    user_goal: str
    current_config: NotRequired[dict[str, Any] | None]
    context: NotRequired[dict[str, Any] | None]
    current_step: str
    target_mode: NotRequired[str | None]
    draft: NotRequired[dict[str, Any] | None]
    compile_response: NotRequired[dict[str, Any] | None]
    compile_payload: NotRequired[dict[str, Any] | None]
    approval_required: bool
    approved_action: NotRequired[str | None]
    workflow_result: NotRequired[dict[str, Any] | None]
    analysis: list[str]
    recommendation: NotRequired[str | None]
    warnings: list[str]
    unsupported: list[str]
    validation_errors: list[str]
    audit_log: list[dict[str, Any]]
    steps: list[str]


def build_research_graph(
    *,
    provider: LLMProvider | None = None,
    workflow_runner: WorkflowRunner | None = None,
) -> Any:
    """Build a LangGraph state machine for the research workflow."""
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise ResearchGraphDependencyError(
            "LangGraph is required to run the Research Copilot graph. Install the backend agents extra or requirements.txt."
        ) from exc

    graph: Any = StateGraph(_GraphState)
    graph.add_node("interpret_research_goal", _wrap_node(nodes.interpret_research_goal))
    graph.add_node("draft_strategy", _wrap_node(lambda state: nodes.draft_strategy(state, provider)))
    graph.add_node("validate_draft", _wrap_node(nodes.validate_draft))
    graph.add_node("compile_request", _wrap_node(nodes.compile_request))
    graph.add_node("await_user_approval", _wrap_node(nodes.await_user_approval))
    graph.add_node("run_workflow", _wrap_node(lambda state: nodes.optionally_run_workflow(state, workflow_runner)))
    graph.add_node("analyze_results", _wrap_node(nodes.analyze_results))
    graph.add_node("recommend_next_step", _wrap_node(nodes.recommend_next_step))

    graph.add_edge(START, "interpret_research_goal")
    graph.add_edge("interpret_research_goal", "draft_strategy")
    graph.add_edge("draft_strategy", "validate_draft")
    graph.add_edge("validate_draft", "compile_request")
    graph.add_edge("compile_request", "await_user_approval")
    graph.add_conditional_edges(
        "await_user_approval",
        _route_after_approval,
        {
            "run_workflow": "run_workflow",
            "recommend_next_step": "recommend_next_step",
            "end": END,
        },
    )
    graph.add_edge("run_workflow", "analyze_results")
    graph.add_edge("analyze_results", "recommend_next_step")
    graph.add_edge("recommend_next_step", END)
    return graph.compile()


def run_research_graph(
    state: ResearchGraphState,
    *,
    provider: LLMProvider | None = None,
    workflow_runner: WorkflowRunner | None = None,
) -> ResearchGraphState:
    """Invoke the Research Copilot graph and return typed state."""
    try:
        graph = build_research_graph(provider=provider, workflow_runner=workflow_runner)
    except ResearchGraphDependencyError:
        return _run_research_graph_locally(state, provider=provider, workflow_runner=workflow_runner)
    result = graph.invoke(state.model_dump(mode="python"))
    return ResearchGraphState.model_validate(result)


def _wrap_node(func: Callable[[ResearchGraphState], ResearchGraphState]) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def wrapped(raw_state: dict[str, Any]) -> dict[str, Any]:
        state = ResearchGraphState.model_validate(raw_state)
        next_state = func(state)
        return next_state.model_dump(mode="python")

    return wrapped


def _route_after_approval(raw_state: dict[str, Any]) -> str:
    state = ResearchGraphState.model_validate(raw_state)
    if state.validation_errors:
        return "recommend_next_step"
    if state.compile_payload is None:
        return "recommend_next_step"
    if state.approved_action is None:
        return "end"
    if state.approval_required:
        return "recommend_next_step"
    return "run_workflow"


def _run_research_graph_locally(
    state: ResearchGraphState,
    *,
    provider: LLMProvider | None,
    workflow_runner: WorkflowRunner | None,
) -> ResearchGraphState:
    """Run the same explicit transitions when LangGraph is not installed locally."""
    current = nodes.interpret_research_goal(state)
    current = nodes.draft_strategy(current, provider)
    current = nodes.validate_draft(current)
    current = nodes.compile_request(current)
    current = nodes.await_user_approval(current)
    route = _route_after_approval(current.model_dump(mode="python"))
    if route == "end":
        return current
    if route == "recommend_next_step":
        return nodes.recommend_next_step(current)

    current = nodes.optionally_run_workflow(current, workflow_runner)
    current = nodes.analyze_results(current)
    return nodes.recommend_next_step(current)
