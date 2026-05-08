"""Typed state for the backend Research Copilot graph."""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backtester.ai.schemas import StrategyCompileResponse, StrategyDraft, TargetMode


class ResearchStep(str, Enum):
    """Explicit graph transition names."""

    INTERPRET_RESEARCH_GOAL = "interpret_research_goal"
    DRAFT_STRATEGY = "draft_strategy"
    VALIDATE_DRAFT = "validate_draft"
    COMPILE_REQUEST = "compile_request"
    AWAIT_USER_APPROVAL = "await_user_approval"
    RUN_WORKFLOW = "run_workflow"
    ANALYZE_RESULTS = "analyze_results"
    RECOMMEND_NEXT_STEP = "recommend_next_step"


class ApprovedAction(str, Enum):
    """Workflow actions a caller may explicitly approve."""

    RUN_BACKTEST = "run_backtest"
    RUN_GRID_SEARCH = "run_grid_search"
    RUN_WALK_FORWARD = "run_walk_forward"


class AuditEvent(BaseModel):
    """One concise state-transition audit record."""

    model_config = ConfigDict(extra="forbid")

    step: ResearchStep
    message: str


class WorkflowResultSummary(BaseModel):
    """API-friendly placeholder summary for executed workflow results."""

    model_config = ConfigDict(extra="forbid")

    target_mode: TargetMode
    status: str = "completed"
    summary: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ResearchGraphState(BaseModel):
    """Serializable state passed between Research Copilot graph nodes."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    session_id: str = Field(default_factory=lambda: str(uuid4()))
    user_goal: str
    current_config: dict[str, Any] | None = None
    context: dict[str, Any] | None = None
    current_step: ResearchStep = ResearchStep.INTERPRET_RESEARCH_GOAL
    target_mode: TargetMode | None = None
    draft: StrategyDraft | None = None
    compile_response: StrategyCompileResponse | None = None
    compile_payload: dict[str, Any] | None = None
    approval_required: bool = False
    approved_action: ApprovedAction | None = None
    workflow_result: WorkflowResultSummary | None = None
    analysis: list[str] = Field(default_factory=list)
    recommendation: str | None = None
    warnings: list[str] = Field(default_factory=list)
    unsupported: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    audit_log: list[AuditEvent] = Field(default_factory=list)
    steps: list[ResearchStep] = Field(default_factory=list)

    @field_validator("user_goal")
    @classmethod
    def strip_user_goal(cls, value: str) -> str:
        """Normalize whitespace while preserving intent."""
        normalized = value.strip()
        if not normalized:
            msg = "user_goal must not be empty."
            raise ValueError(msg)
        return normalized

    def add_event(self, step: ResearchStep, message: str) -> "ResearchGraphState":
        """Return a copied state with an appended audit event."""
        steps = [*self.steps, step]
        audit_log = [*self.audit_log, AuditEvent(step=step, message=message)]
        return self.model_copy(update={"current_step": step, "steps": steps, "audit_log": audit_log})

    def append_warnings(self, values: list[str]) -> "ResearchGraphState":
        """Return a copied state with unique appended warnings."""
        return self.model_copy(update={"warnings": _unique_strings([*self.warnings, *values])})

    def append_unsupported(self, values: list[str]) -> "ResearchGraphState":
        """Return a copied state with unique appended unsupported items."""
        return self.model_copy(update={"unsupported": _unique_strings([*self.unsupported, *values])})

    def append_validation_errors(self, values: list[str]) -> "ResearchGraphState":
        """Return a copied state with unique appended validation errors."""
        return self.model_copy(update={"validation_errors": _unique_strings([*self.validation_errors, *values])})


def action_for_target_mode(target_mode: TargetMode) -> ApprovedAction | None:
    """Return the explicit approval action required for a target mode."""
    if target_mode == TargetMode.SINGLE_RUN:
        return ApprovedAction.RUN_BACKTEST
    if target_mode == TargetMode.GRID_SEARCH:
        return ApprovedAction.RUN_GRID_SEARCH
    if target_mode == TargetMode.WALK_FORWARD:
        return ApprovedAction.RUN_WALK_FORWARD
    return None


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return unique
