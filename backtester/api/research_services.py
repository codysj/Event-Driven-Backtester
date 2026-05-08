"""Service helpers for Research Copilot API endpoints."""

from __future__ import annotations

from backtester.agents import ResearchGraphState, run_research_graph
from backtester.api.research_schemas import (
    ResearchApprovalRequest,
    ResearchGraphResponse,
    ResearchPlanRequest,
    ResearchStatus,
)


def plan_research_from_request(request: ResearchPlanRequest) -> ResearchGraphResponse:
    """Draft and compile a research plan, stopping before workflow execution."""
    state = ResearchGraphState(
        user_goal=request.user_goal,
        current_config=request.current_config,
        context=request.context,
    )
    result = run_research_graph(state)
    return _response_from_state(result)


def approve_research_from_request(request: ResearchApprovalRequest) -> ResearchGraphResponse:
    """Resume a prior state and run at most one explicitly approved workflow."""
    state = _state_from_response(request.state)
    if state.workflow_result is not None:
        result = state.append_validation_errors(
            ["This research state already contains a workflow result. Start a new plan before approving another run."]
        )
        return _response_from_state(result)

    approved_state = state.model_copy(update={"approved_action": request.approved_action})
    result = run_research_graph(approved_state)
    return _response_from_state(result)


def _state_from_response(response: ResearchGraphResponse) -> ResearchGraphState:
    return ResearchGraphState(
        session_id=response.session_id,
        user_goal=response.user_goal,
        current_step=response.current_step,
        target_mode=response.target_mode,
        draft=response.draft,
        compile_response=response.compile_response,
        compile_payload=response.compile_payload,
        approval_required=response.approval_required,
        approved_action=response.approved_action,
        workflow_result=response.workflow_result,
        analysis=response.analysis,
        recommendation=response.recommendation,
        warnings=response.warnings,
        unsupported=response.unsupported,
        validation_errors=response.validation_errors,
        audit_log=response.audit_log,
        steps=response.steps,
    )


def _response_from_state(state: ResearchGraphState) -> ResearchGraphResponse:
    return ResearchGraphResponse(
        session_id=state.session_id,
        user_goal=state.user_goal,
        status=_status_from_state(state),
        current_step=state.current_step,
        target_mode=state.target_mode,
        steps=state.steps,
        draft=state.draft,
        compile_response=state.compile_response,
        compile_payload=state.compile_payload,
        approval_required=state.approval_required,
        approved_action=state.approved_action,
        workflow_result=state.workflow_result,
        analysis=state.analysis,
        recommendation=state.recommendation,
        warnings=state.warnings,
        unsupported=state.unsupported,
        validation_errors=state.validation_errors,
        audit_log=state.audit_log,
    )


def _status_from_state(state: ResearchGraphState) -> ResearchStatus:
    if state.workflow_result is not None:
        return "completed"
    if state.validation_errors:
        return "blocked"
    if state.approval_required:
        return "awaiting_approval"
    return "drafted"
