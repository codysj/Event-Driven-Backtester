"""Provider abstraction and deterministic fake strategy-draft provider."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Protocol, TypeAlias

from pydantic import ValidationError

from backtester.ai.schemas import (
    StrategyDraft,
    StrategyDraftRequest,
    StrategyDraftResponse,
    StrategyDraftStatus,
    StrategyKind,
    TargetMode,
)
from backtester.ai.validator import validate_strategy_draft


ProviderDraft: TypeAlias = StrategyDraft | Mapping[str, object]


class LLMProvider(Protocol):
    """Protocol for future real LLM providers."""

    def draft_strategy(self, request: StrategyDraftRequest) -> ProviderDraft:
        """Return a structured strategy draft or provider JSON mapping."""


class FakeStrategyDraftProvider:
    """Deterministic local provider used until a real LLM is introduced."""

    unsupported_terms = (
        "options flow",
        "live trading",
        "intraday",
        "minute bars",
        "twitter sentiment",
        "broker execution",
        "broker",
        "multi-asset",
        "multi asset",
        "portfolio",
        "ignore previous",
        "output python code",
        "python code",
        "generate code",
    )

    def draft_strategy(self, request: StrategyDraftRequest) -> StrategyDraft:
        """Draft a strategy using deterministic pattern matching."""
        prompt = request.prompt
        lowered = prompt.lower()
        matched_unsupported = [term for term in self.unsupported_terms if term in lowered]
        if matched_unsupported:
            return StrategyDraft(
                target_mode=TargetMode.UNSPECIFIED,
                strategy_kind=StrategyKind.UNSUPPORTED,
                assumptions=[],
                warnings=[
                    "The request includes unsupported or unsafe concepts for the v1 builder.",
                    "The builder returns inert data only and will not generate executable code.",
                ],
                unsupported=matched_unsupported,
                confidence=0.9,
                status=StrategyDraftStatus.UNSUPPORTED,
            )

        if "mean reversion" in lowered:
            return self._mean_reversion_draft(prompt)
        if "sma" in lowered or "crossover" in lowered or "moving average" in lowered:
            return self._momentum_draft(prompt)

        return StrategyDraft(
            target_mode=TargetMode.UNSPECIFIED,
            strategy_kind=StrategyKind.UNSUPPORTED,
            warnings=["The request did not match a supported v1 strategy pattern."],
            unsupported=["Only momentum SMA crossover and mean reversion drafts are supported in v1."],
            confidence=0.35,
            status=StrategyDraftStatus.NEEDS_CLARIFICATION,
        )

    def _momentum_draft(self, prompt: str) -> StrategyDraft:
        ticker = _extract_ticker(prompt)
        start_date, end_date = _extract_date_range(prompt)
        fast_window, slow_window = _extract_sma_windows(prompt)
        assumptions = _date_assumptions(start_date, end_date)
        if fast_window is None or slow_window is None:
            return StrategyDraft(
                target_mode=TargetMode.SINGLE_RUN,
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                strategy_kind=StrategyKind.MOMENTUM,
                parameters={},
                assumptions=assumptions,
                warnings=["Could not identify both fast and slow SMA windows."],
                confidence=0.45,
                status=StrategyDraftStatus.NEEDS_CLARIFICATION,
            )
        return StrategyDraft(
            target_mode=TargetMode.SINGLE_RUN,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            strategy_kind=StrategyKind.MOMENTUM,
            parameters={"fast_window": fast_window, "slow_window": slow_window},
            assumptions=assumptions,
            warnings=["Draft only. Review before compiling or running a backtest."],
            confidence=0.82,
            status=StrategyDraftStatus.READY,
        )

    def _mean_reversion_draft(self, prompt: str) -> StrategyDraft:
        ticker = _extract_ticker(prompt)
        start_date, end_date = _extract_date_range(prompt)
        window = _extract_window(prompt)
        num_std = _extract_num_std(prompt)
        assumptions = _date_assumptions(start_date, end_date)
        if window is None or num_std is None:
            return StrategyDraft(
                target_mode=TargetMode.SINGLE_RUN,
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                strategy_kind=StrategyKind.MEAN_REVERSION,
                parameters={},
                assumptions=assumptions,
                warnings=["Could not identify both mean-reversion window and standard deviation band."],
                confidence=0.45,
                status=StrategyDraftStatus.NEEDS_CLARIFICATION,
            )
        return StrategyDraft(
            target_mode=TargetMode.SINGLE_RUN,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            strategy_kind=StrategyKind.MEAN_REVERSION,
            parameters={"window": window, "num_std": num_std},
            assumptions=assumptions,
            warnings=["Draft only. Review before compiling or running a backtest."],
            confidence=0.82,
            status=StrategyDraftStatus.READY,
        )


def draft_strategy_from_request(
    request: StrategyDraftRequest,
    provider: LLMProvider | None = None,
) -> StrategyDraftResponse:
    """Create and validate a strategy draft from a natural-language request."""
    selected_provider = provider or FakeStrategyDraftProvider()
    try:
        draft = _coerce_provider_output(selected_provider.draft_strategy(request))
    except ValueError as exc:
        return StrategyDraftResponse(
            draft=None,
            status=StrategyDraftStatus.NEEDS_CLARIFICATION,
            warnings=["Provider returned an invalid strategy draft."],
            unsupported=[],
            validation_errors=[str(exc)],
        )

    validation = validate_strategy_draft(draft)
    warnings = _unique_strings([*draft.warnings, *validation.warnings])
    unsupported = _unique_strings([*draft.unsupported, *validation.unsupported])
    status = draft.status
    if validation.errors:
        status = (
            StrategyDraftStatus.UNSUPPORTED
            if draft.status == StrategyDraftStatus.UNSUPPORTED
            else StrategyDraftStatus.NEEDS_CLARIFICATION
        )
    elif unsupported and draft.status != StrategyDraftStatus.UNSUPPORTED:
        status = StrategyDraftStatus.NEEDS_CLARIFICATION

    response_draft = draft.model_copy(update={"status": status, "warnings": warnings, "unsupported": unsupported})
    return StrategyDraftResponse(
        draft=response_draft,
        status=status,
        warnings=warnings,
        unsupported=unsupported,
        validation_errors=validation.errors,
    )


def _coerce_provider_output(output: ProviderDraft) -> StrategyDraft:
    if isinstance(output, StrategyDraft):
        return output
    try:
        return StrategyDraft.model_validate(output)
    except ValidationError as exc:
        errors = "; ".join(str(error["msg"]) for error in exc.errors())
        raise ValueError(errors) from exc


def _extract_ticker(prompt: str) -> str | None:
    matches = re.findall(r"\b[A-Z]{1,5}\b", prompt)
    ignored = {"SMA", "ETF"}
    return next((match for match in matches if match not in ignored), None)


def _extract_date_range(prompt: str) -> tuple[str | None, str | None]:
    iso_dates = re.findall(r"\b(19\d{2}|20\d{2})-(\d{2})-(\d{2})\b", prompt)
    if len(iso_dates) >= 2:
        first = "-".join(iso_dates[0])
        second = "-".join(iso_dates[1])
        return first, second

    years = [int(year) for year in re.findall(r"\b(19\d{2}|20\d{2})\b", prompt)]
    if len(years) >= 2:
        return f"{years[0]}-01-01", f"{years[1]}-12-31"
    return None, None


def _extract_sma_windows(prompt: str) -> tuple[int | None, int | None]:
    slash_match = re.search(r"\b(\d{1,4})\s*/\s*(\d{1,4})\s*SMA\b", prompt, re.IGNORECASE)
    if slash_match is not None:
        return int(slash_match.group(1)), int(slash_match.group(2))
    crossover_match = re.search(
        r"\b(\d{1,4})\s*(?:day|-day)?\s*(?:SMA|moving average)?.{0,30}\b(\d{1,4})\s*(?:day|-day)?\s*(?:SMA|moving average|crossover)",
        prompt,
        re.IGNORECASE,
    )
    if crossover_match is not None:
        return int(crossover_match.group(1)), int(crossover_match.group(2))
    return None, None


def _extract_window(prompt: str) -> int | None:
    match = re.search(r"\b(\d{1,4})\s*(?:day|-day)\s+window\b", prompt, re.IGNORECASE)
    if match is not None:
        return int(match.group(1))
    match = re.search(r"\bwindow\s+(?:of\s+)?(\d{1,4})\b", prompt, re.IGNORECASE)
    return int(match.group(1)) if match is not None else None


def _extract_num_std(prompt: str) -> float | None:
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:standard deviation|std|sigma)", prompt, re.IGNORECASE)
    return float(match.group(1)) if match is not None else None


def _date_assumptions(start_date: str | None, end_date: str | None) -> list[str]:
    if start_date is not None and end_date is not None:
        return []
    return ["No complete date range was provided; compilation should request or apply reviewed defaults."]


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            unique.append(value)
            seen.add(value)
    return unique
