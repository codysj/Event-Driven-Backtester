"""Small testable nodes for the Research Copilot graph."""

from __future__ import annotations

from backtester.agents.research_state import (
    ApprovedAction,
    ResearchGraphState,
    ResearchStep,
    action_for_target_mode,
)
from backtester.agents.tools import (
    ServiceWorkflowRunner,
    WorkflowRunner,
    analyze_workflow_summary,
    run_approved_workflow,
    summarize_workflow_result,
)
from backtester.ai import LLMProvider, compile_strategy_draft, draft_strategy_from_request, validate_strategy_draft
from backtester.ai.schemas import StrategyDraftRequest, StrategyDraftStatus, TargetMode


def interpret_research_goal(state: ResearchGraphState) -> ResearchGraphState:
    """Record the user goal without executing anything."""
    return state.add_event(ResearchStep.INTERPRET_RESEARCH_GOAL, "Captured research goal for safe orchestration.")


def draft_strategy(state: ResearchGraphState, provider: LLMProvider | None = None) -> ResearchGraphState:
    """Draft an inert strategy through the existing AI provider boundary."""
    if state.draft is not None:
        return state.add_event(ResearchStep.DRAFT_STRATEGY, "Reused existing inert strategy draft.")

    response = draft_strategy_from_request(StrategyDraftRequest(prompt=state.user_goal), provider)
    next_state = state.model_copy(
        update={
            "draft": response.draft,
            "target_mode": response.draft.target_mode if response.draft is not None else state.target_mode,
        }
    )
    next_state = next_state.append_warnings(response.warnings)
    next_state = next_state.append_unsupported(response.unsupported)
    next_state = next_state.append_validation_errors(response.validation_errors)
    return next_state.add_event(ResearchStep.DRAFT_STRATEGY, f"Draft status is {response.status.value}.")


def validate_draft(state: ResearchGraphState) -> ResearchGraphState:
    """Run semantic validation over the inert draft."""
    if state.draft is None:
        next_state = state.append_validation_errors(["No draft is available to validate."])
        return next_state.add_event(ResearchStep.VALIDATE_DRAFT, "Draft validation could not run.")

    validation = validate_strategy_draft(state.draft)
    next_state = state.append_warnings(validation.warnings)
    next_state = next_state.append_unsupported(validation.unsupported)
    next_state = next_state.append_validation_errors(validation.errors)
    message = "Draft validation passed." if validation.is_valid else "Draft validation found issues."
    return next_state.add_event(ResearchStep.VALIDATE_DRAFT, message)


def compile_request(state: ResearchGraphState) -> ResearchGraphState:
    """Compile an inert draft into an existing API request payload."""
    if state.compile_response is not None:
        return state.add_event(ResearchStep.COMPILE_REQUEST, "Reused existing compiled request payload.")
    if state.draft is None:
        next_state = state.append_validation_errors(["No draft is available to compile."])
        return next_state.add_event(ResearchStep.COMPILE_REQUEST, "Compile skipped because no draft exists.")

    response = compile_strategy_draft(state.draft)
    payload = response.payload if response.payload is not None else None
    approval_required = response.status == StrategyDraftStatus.READY and payload is not None
    next_state = state.model_copy(
        update={
            "compile_response": response,
            "compile_payload": payload,
            "target_mode": response.target_mode,
            "approval_required": approval_required,
        }
    )
    next_state = next_state.append_warnings(response.warnings)
    next_state = next_state.append_unsupported(response.unsupported)
    next_state = next_state.append_validation_errors(response.validation_errors)
    message = "Compiled payload is ready for approval." if approval_required else "Compile did not produce a runnable payload."
    return next_state.add_event(ResearchStep.COMPILE_REQUEST, message)


def await_user_approval(state: ResearchGraphState) -> ResearchGraphState:
    """Stop unless a matching explicit approval action is present."""
    if state.compile_payload is None or state.target_mode is None:
        next_state = state.model_copy(update={"approval_required": False})
        return next_state.add_event(ResearchStep.AWAIT_USER_APPROVAL, "No compiled payload is awaiting approval.")

    required_action = action_for_target_mode(state.target_mode)
    if required_action is None:
        next_state = state.append_validation_errors(["Compiled target mode is not executable."])
        next_state = next_state.model_copy(update={"approval_required": False})
        return next_state.add_event(ResearchStep.AWAIT_USER_APPROVAL, "Compiled target is not executable.")

    if state.approved_action is None:
        next_state = state.model_copy(
            update={
                "approval_required": True,
                "recommendation": f"Review the compiled payload, then approve {required_action.value} to continue.",
            }
        )
        return next_state.add_event(ResearchStep.AWAIT_USER_APPROVAL, "Stopped before workflow execution.")

    if state.approved_action != required_action:
        message = f"approved_action must be {required_action.value} for target_mode {state.target_mode.value}."
        next_state = state.append_validation_errors([message])
        next_state = next_state.model_copy(update={"approval_required": True})
        return next_state.add_event(ResearchStep.AWAIT_USER_APPROVAL, "Approval did not match compiled target mode.")

    next_state = state.model_copy(update={"approval_required": False})
    return next_state.add_event(ResearchStep.AWAIT_USER_APPROVAL, "Explicit approval accepted.")


def optionally_run_workflow(
    state: ResearchGraphState,
    runner: WorkflowRunner | None = None,
) -> ResearchGraphState:
    """Run exactly one approved workflow through safe service wrappers."""
    if state.compile_payload is None or state.target_mode is None or state.approved_action is None:
        return state.add_event(ResearchStep.RUN_WORKFLOW, "No approved workflow was run.")
    if state.validation_errors:
        return state.add_event(ResearchStep.RUN_WORKFLOW, "Workflow run skipped because validation errors exist.")

    selected_runner = runner or ServiceWorkflowRunner()
    try:
        result = run_approved_workflow(state.target_mode, state.approved_action, state.compile_payload, selected_runner)
    except ValueError as exc:
        next_state = state.append_validation_errors([str(exc)])
        return next_state.add_event(ResearchStep.RUN_WORKFLOW, "Workflow run was rejected.")

    summary = summarize_workflow_result(state.target_mode, result)
    next_state = state.model_copy(update={"workflow_result": summary})
    return next_state.add_event(ResearchStep.RUN_WORKFLOW, f"Ran approved action {state.approved_action.value}.")


def analyze_results(state: ResearchGraphState) -> ResearchGraphState:
    """Analyze a completed workflow with deterministic heuristics."""
    if state.workflow_result is None:
        return state.add_event(ResearchStep.ANALYZE_RESULTS, "No workflow result is available to analyze.")

    notes = analyze_workflow_summary(state.workflow_result)
    next_state = state.model_copy(update={"analysis": notes})
    return next_state.add_event(ResearchStep.ANALYZE_RESULTS, "Recorded deterministic first-pass analysis.")


def recommend_next_step(state: ResearchGraphState) -> ResearchGraphState:
    """Recommend the next safe human-reviewed step."""
    if state.validation_errors:
        recommendation = "Resolve validation errors before compiling or approving a workflow run."
    elif state.approval_required:
        required = action_for_target_mode(state.target_mode or TargetMode.UNSPECIFIED)
        action_text = required.value if isinstance(required, ApprovedAction) else "the matching run action"
        recommendation = f"Review the inert payload and explicitly approve {action_text} if it matches your intent."
    elif state.workflow_result is not None:
        recommendation = "Review the heuristic analysis before changing parameters or running another workflow."
    else:
        recommendation = "Clarify the research goal or strategy parameters before continuing."

    next_state = state.model_copy(update={"recommendation": recommendation})
    return next_state.add_event(ResearchStep.RECOMMEND_NEXT_STEP, "Recommended the next safe step.")
