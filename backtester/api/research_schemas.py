"""Pydantic schemas for Research Copilot API endpoints."""

from __future__ import annotations

from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backtester.agents import ApprovedAction, ResearchStep, WorkflowResultSummary
from backtester.agents.research_state import AuditEvent
from backtester.ai.schemas import StrategyCompileResponse, StrategyDraft, TargetMode


ResearchStatus: TypeAlias = Literal["awaiting_approval", "completed", "blocked", "drafted"]


class ResearchPlanRequest(BaseModel):
    """Request to draft and compile a research plan without execution."""

    model_config = ConfigDict(extra="forbid")

    user_goal: str = Field(..., min_length=1)
    current_config: dict[str, Any] | None = None
    context: dict[str, Any] | None = None

    @field_validator("user_goal")
    @classmethod
    def strip_user_goal(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "user_goal must not be empty."
            raise ValueError(msg)
        return normalized


class ResearchGraphResponse(BaseModel):
    """Sanitized, JSON-friendly Research Copilot state returned to clients."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    user_goal: str
    status: ResearchStatus
    current_step: ResearchStep
    target_mode: TargetMode | None = None
    steps: list[ResearchStep] = Field(default_factory=list)
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


class ResearchApprovalRequest(BaseModel):
    """Request to resume a prior response state with one explicit approval."""

    model_config = ConfigDict(extra="forbid")

    state: ResearchGraphResponse
    approved_action: ApprovedAction


ResearchPlanResponse = ResearchGraphResponse
ResearchApprovalResponse = ResearchGraphResponse
