"""Provider abstraction and strategy-draft provider implementations."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, TypeAlias, cast

import httpx

from pydantic import ValidationError

from backtester.ai.prompts import STRATEGY_DRAFT_SYSTEM_PROMPT
from backtester.ai.schemas import (
    StrategyDraft,
    StrategyDraftRequest,
    StrategyDraftResponse,
    StrategyDraftStatus,
    StrategyKind,
    TargetMode,
)
from backtester.ai.validator import validate_strategy_draft
from backtester.strategy.rule_schema import (
    ConditionOperator,
    ConditionSpec,
    IndicatorName,
    IndicatorSpec,
    RuleBasedStrategySpec,
    RuleSetSpec,
)


ProviderDraft: TypeAlias = StrategyDraft | Mapping[str, object]
DEFAULT_OPENAI_COMPATIBLE_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_COMPATIBLE_MODEL = "gpt-4o-mini"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"
DEFAULT_PROVIDER_TIMEOUT_SECONDS = 30.0


class ProviderConfigurationError(ValueError):
    """Raised when the selected provider is disabled or misconfigured."""


class ProviderRequestError(RuntimeError):
    """Raised when a provider request fails safely."""


class ProviderTimeoutError(ProviderRequestError):
    """Raised when a provider request times out."""


@dataclass(frozen=True)
class StrategyDraftProviderConfig:
    """Environment-derived provider settings."""

    enabled: bool = True
    provider: str = "fake"
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    timeout_seconds: float = DEFAULT_PROVIDER_TIMEOUT_SECONDS


class LLMProvider(Protocol):
    """Protocol for strategy-draft providers."""

    def draft_strategy(self, request: StrategyDraftRequest) -> ProviderDraft:
        """Return a structured strategy draft or provider JSON mapping."""


class HttpChatClient(Protocol):
    """Small subset of httpx.Client used by the provider."""

    def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        json: Mapping[str, object],
    ) -> httpx.Response:
        """POST a chat completion request."""


class FakeStrategyDraftProvider:
    """Deterministic local provider used by default and in tests."""

    unsupported_terms = (
        "options flow",
        "live trading",
        "intraday",
        "minute bars",
        "twitter sentiment",
        "broker execution",
        "broker",
        "eval",
        "exec",
        "lambda",
        "__",
        "import ",
        "subprocess",
        "shell command",
        "powershell",
        "cmd.exe",
        "filesystem",
        "file path",
        "write file",
        "multi-asset",
        "multi asset",
        "portfolio",
        "ignore previous",
        "python",
        "output python code",
        "python code",
        "generate code",
    )

    def draft_strategy(self, request: StrategyDraftRequest) -> StrategyDraft:
        """Draft a strategy using deterministic pattern matching."""
        prompt = request.prompt
        lowered = prompt.lower()
        matched_unsupported = [term for term in self.unsupported_terms if term in lowered]
        if _contains_filesystem_path(prompt):
            matched_unsupported.append("filesystem path")
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

        rule_based_draft = self._rule_based_draft(prompt)
        if rule_based_draft is not None:
            return rule_based_draft
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
        target_mode = _target_mode_from_prompt(prompt)
        ticker = _extract_ticker(prompt)
        start_date, end_date = _extract_date_range(prompt)
        fast_window, slow_window = _extract_sma_windows(prompt)
        assumptions = _date_assumptions(start_date, end_date)
        if fast_window is None or slow_window is None:
            return StrategyDraft(
                target_mode=target_mode,
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
            target_mode=target_mode,
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

    def _rule_based_draft(self, prompt: str) -> StrategyDraft | None:
        lowered = prompt.lower()
        has_entry_exit_language = _has_rule_action(lowered, "buy", "enter") and _has_rule_action(
            lowered,
            "sell",
            "exit",
        )
        if not has_entry_exit_language:
            return None

        if "sma" in lowered and ("crosses above" in lowered or "cross above" in lowered):
            window = _extract_single_indicator_window(prompt, "SMA")
            if window is None:
                return self._rule_based_needs_clarification(prompt, "Could not identify the SMA window.")
            return self._rule_based_ready(
                prompt,
                entry=ConditionSpec(
                    left=_close_indicator(),
                    operator=ConditionOperator.CROSSES_ABOVE,
                    right=IndicatorSpec(name=IndicatorName.SMA, window=window),
                ),
                exit_condition=ConditionSpec(
                    left=_close_indicator(),
                    operator=ConditionOperator.CROSSES_BELOW,
                    right=IndicatorSpec(name=IndicatorName.SMA, window=window),
                ),
            )

        if "bollinger" in lowered and "lower" in lowered and "upper" in lowered:
            window = _extract_single_indicator_window(prompt, "Bollinger") or _extract_window(prompt)
            num_std = _extract_num_std(prompt)
            if window is None or num_std is None:
                return self._rule_based_needs_clarification(
                    prompt,
                    "Could not identify both Bollinger window and standard deviation band.",
                )
            return self._rule_based_ready(
                prompt,
                entry=ConditionSpec(
                    left=_close_indicator(),
                    operator=ConditionOperator.LTE,
                    right=IndicatorSpec(name=IndicatorName.BOLLINGER_LOWER, window=window, num_std=num_std),
                ),
                exit_condition=ConditionSpec(
                    left=_close_indicator(),
                    operator=ConditionOperator.GTE,
                    right=IndicatorSpec(name=IndicatorName.BOLLINGER_UPPER, window=window, num_std=num_std),
                ),
            )

        if "rolling high" in lowered or "new high" in lowered or "breakout" in lowered:
            window = _extract_single_indicator_window(prompt, "rolling high") or _extract_new_high_window(prompt)
            if window is None:
                return self._rule_based_needs_clarification(prompt, "Could not identify the rolling high window.")
            exit_window = _extract_single_indicator_window(prompt, "SMA") or window
            warnings = []
            if "sell when" not in lowered and "exit when" not in lowered:
                warnings.append("Exit rule was inferred as close crossing below the same-window SMA.")
            return self._rule_based_ready(
                prompt,
                entry=ConditionSpec(
                    left=_close_indicator(),
                    operator=ConditionOperator.GT,
                    right=IndicatorSpec(name=IndicatorName.ROLLING_HIGH, window=window),
                ),
                exit_condition=ConditionSpec(
                    left=_close_indicator(),
                    operator=ConditionOperator.CROSSES_BELOW,
                    right=IndicatorSpec(name=IndicatorName.SMA, window=exit_window),
                ),
                extra_warnings=warnings,
            )

        return None

    def _rule_based_ready(
        self,
        prompt: str,
        *,
        entry: ConditionSpec,
        exit_condition: ConditionSpec,
        extra_warnings: list[str] | None = None,
    ) -> StrategyDraft:
        start_date, end_date = _extract_date_range(prompt)
        warnings = [
            "Rule-based draft only. Entry conditions use ALL logic; exit conditions use ANY logic.",
            *(extra_warnings or []),
        ]
        return StrategyDraft(
            target_mode=TargetMode.SINGLE_RUN,
            ticker=_extract_ticker(prompt),
            start_date=start_date,
            end_date=end_date,
            strategy_kind=StrategyKind.RULE_BASED,
            rule_spec=RuleBasedStrategySpec(rules=RuleSetSpec(entry=[entry], exit=[exit_condition])),
            assumptions=_date_assumptions(start_date, end_date),
            warnings=warnings,
            confidence=0.78,
            status=StrategyDraftStatus.READY,
        )

    def _rule_based_needs_clarification(self, prompt: str, warning: str) -> StrategyDraft:
        start_date, end_date = _extract_date_range(prompt)
        return StrategyDraft(
            target_mode=TargetMode.SINGLE_RUN,
            ticker=_extract_ticker(prompt),
            start_date=start_date,
            end_date=end_date,
            strategy_kind=StrategyKind.RULE_BASED,
            assumptions=_date_assumptions(start_date, end_date),
            warnings=[warning],
            confidence=0.45,
            status=StrategyDraftStatus.NEEDS_CLARIFICATION,
        )

    def _mean_reversion_draft(self, prompt: str) -> StrategyDraft:
        target_mode = _target_mode_from_prompt(prompt)
        ticker = _extract_ticker(prompt)
        start_date, end_date = _extract_date_range(prompt)
        window = _extract_window(prompt)
        num_std = _extract_num_std(prompt)
        assumptions = _date_assumptions(start_date, end_date)
        if window is None or num_std is None:
            return StrategyDraft(
                target_mode=target_mode,
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
            target_mode=target_mode,
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


class OpenAICompatibleStrategyDraftProvider:
    """Strategy-draft provider for OpenAI-compatible chat completion APIs."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str = DEFAULT_OPENAI_COMPATIBLE_BASE_URL,
        timeout_seconds: float = DEFAULT_PROVIDER_TIMEOUT_SECONDS,
        http_client: HttpChatClient | None = None,
        provider_name: str = "openai_compatible",
    ) -> None:
        if not api_key.strip():
            raise ProviderConfigurationError("BACKTESTER_AI_API_KEY is required for real AI providers.")
        if not model.strip():
            raise ProviderConfigurationError("BACKTESTER_AI_MODEL is required for real AI providers.")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.http_client = http_client
        self.provider_name = provider_name

    def draft_strategy(self, request: StrategyDraftRequest) -> ProviderDraft:
        """Request a structured draft from an OpenAI-compatible chat endpoint."""
        payload: dict[str, object] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": STRATEGY_DRAFT_SYSTEM_PROMPT},
                {"role": "user", "content": request.prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        response = self._post_chat_completion(payload)
        content = _extract_chat_message_content(response)
        return _parse_provider_json(content)

    def _post_chat_completion(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = self._send_post(url, headers, payload)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError("AI provider timed out while drafting the strategy.") from exc
        except httpx.HTTPError as exc:
            raise ProviderRequestError("AI provider request failed.") from exc

        if response.status_code in {401, 403}:
            raise ProviderConfigurationError("AI provider rejected the configured server-side credentials.")
        if response.status_code == 429:
            raise ProviderRequestError("AI provider rate limit was reached. Try again later.")
        if response.status_code >= 400:
            raise ProviderRequestError(f"AI provider returned HTTP {response.status_code}.")

        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderRequestError("AI provider returned a non-JSON HTTP response.") from exc
        if not isinstance(data, Mapping):
            raise ProviderRequestError("AI provider returned an unexpected response shape.")
        return cast(Mapping[str, object], data)

    def _send_post(
        self,
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
    ) -> httpx.Response:
        if self.http_client is not None:
            return self.http_client.post(url, headers=headers, json=payload)
        with httpx.Client(timeout=self.timeout_seconds) as client:
            return client.post(url, headers=headers, json=payload)


def get_strategy_draft_provider(
    env: Mapping[str, str] | None = None,
    *,
    prefer_fake_in_tests: bool = True,
) -> LLMProvider:
    """Build the configured provider without exposing server-side secrets."""
    if env is None and prefer_fake_in_tests and _running_under_pytest():
        return FakeStrategyDraftProvider()

    config = _provider_config_from_env(os.environ if env is None else env)
    if not config.enabled:
        raise ProviderConfigurationError(
            "AI Strategy Builder is disabled. Set BACKTESTER_AI_ENABLED=true to enable provider-backed drafting."
        )

    provider = config.provider
    if provider == "fake":
        return FakeStrategyDraftProvider()
    if provider == "deepseek":
        return _openai_compatible_provider(
            config,
            default_base_url=DEFAULT_DEEPSEEK_BASE_URL,
            default_model=DEFAULT_DEEPSEEK_MODEL,
            provider_name="deepseek",
        )
    if provider == "openai_compatible":
        return _openai_compatible_provider(
            config,
            default_base_url=DEFAULT_OPENAI_COMPATIBLE_BASE_URL,
            default_model=DEFAULT_OPENAI_COMPATIBLE_MODEL,
            provider_name="openai_compatible",
        )

    raise ProviderConfigurationError(
        "Unsupported BACKTESTER_AI_PROVIDER. Use fake, deepseek, or openai_compatible."
    )


def draft_strategy_from_request(
    request: StrategyDraftRequest,
    provider: LLMProvider | None = None,
) -> StrategyDraftResponse:
    """Create and validate a strategy draft from a natural-language request."""
    unsafe_terms = _unsupported_terms_in_prompt(request.prompt)
    if unsafe_terms:
        return _response_from_draft(_unsupported_prompt_draft(unsafe_terms))

    try:
        selected_provider = provider or get_strategy_draft_provider()
    except ProviderConfigurationError as exc:
        return StrategyDraftResponse(
            draft=None,
            status=StrategyDraftStatus.NEEDS_CLARIFICATION,
            warnings=["AI provider is not configured for strategy drafting."],
            unsupported=[],
            validation_errors=[str(exc)],
        )

    try:
        draft = _coerce_provider_output(selected_provider.draft_strategy(request))
    except ProviderConfigurationError as exc:
        return StrategyDraftResponse(
            draft=None,
            status=StrategyDraftStatus.NEEDS_CLARIFICATION,
            warnings=["AI provider is not configured for strategy drafting."],
            unsupported=[],
            validation_errors=[str(exc)],
        )
    except ValueError as exc:
        return StrategyDraftResponse(
            draft=None,
            status=StrategyDraftStatus.NEEDS_CLARIFICATION,
            warnings=["Provider returned an invalid strategy draft."],
            unsupported=[],
            validation_errors=[str(exc)],
        )
    except ProviderTimeoutError:
        return StrategyDraftResponse(
            draft=None,
            status=StrategyDraftStatus.NEEDS_CLARIFICATION,
            warnings=["AI provider timed out before returning a draft."],
            unsupported=[],
            validation_errors=["AI provider timed out while drafting the strategy."],
        )
    except ProviderRequestError as exc:
        return StrategyDraftResponse(
            draft=None,
            status=StrategyDraftStatus.NEEDS_CLARIFICATION,
            warnings=["AI provider could not return a strategy draft."],
            unsupported=[],
            validation_errors=[_safe_provider_error(exc)],
        )

    return _response_from_draft(draft)


def _response_from_draft(draft: StrategyDraft) -> StrategyDraftResponse:
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


def _provider_config_from_env(env: Mapping[str, str]) -> StrategyDraftProviderConfig:
    enabled = _parse_bool_env(env.get("BACKTESTER_AI_ENABLED"), default=True)
    timeout_seconds = _parse_timeout_seconds(env.get("BACKTESTER_AI_TIMEOUT_SECONDS"))
    return StrategyDraftProviderConfig(
        enabled=enabled,
        provider=(env.get("BACKTESTER_AI_PROVIDER") or "fake").strip().lower(),
        model=_optional_env(env.get("BACKTESTER_AI_MODEL")),
        api_key=_optional_env(env.get("BACKTESTER_AI_API_KEY")),
        base_url=_optional_env(env.get("BACKTESTER_AI_BASE_URL")),
        timeout_seconds=timeout_seconds,
    )


def _openai_compatible_provider(
    config: StrategyDraftProviderConfig,
    *,
    default_base_url: str,
    default_model: str,
    provider_name: str,
) -> OpenAICompatibleStrategyDraftProvider:
    if config.api_key is None:
        raise ProviderConfigurationError(
            f"BACKTESTER_AI_API_KEY is required when BACKTESTER_AI_PROVIDER={provider_name}."
        )
    return OpenAICompatibleStrategyDraftProvider(
        api_key=config.api_key,
        model=config.model or default_model,
        base_url=config.base_url or default_base_url,
        timeout_seconds=config.timeout_seconds,
        provider_name=provider_name,
    )


def _parse_bool_env(raw: str | None, *, default: bool) -> bool:
    if raw is None or raw.strip() == "":
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ProviderConfigurationError("BACKTESTER_AI_ENABLED must be true or false.")


def _parse_timeout_seconds(raw: str | None) -> float:
    if raw is None or raw.strip() == "":
        return DEFAULT_PROVIDER_TIMEOUT_SECONDS
    try:
        timeout = float(raw)
    except ValueError as exc:
        raise ProviderConfigurationError("BACKTESTER_AI_TIMEOUT_SECONDS must be a positive number.") from exc
    if timeout <= 0:
        raise ProviderConfigurationError("BACKTESTER_AI_TIMEOUT_SECONDS must be a positive number.")
    return timeout


def _optional_env(raw: str | None) -> str | None:
    if raw is None:
        return None
    stripped = raw.strip()
    return stripped or None


def _running_under_pytest() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ


def _coerce_provider_output(output: ProviderDraft) -> StrategyDraft:
    if isinstance(output, StrategyDraft):
        return output
    try:
        return StrategyDraft.model_validate(output)
    except ValidationError as exc:
        errors = "; ".join(str(error["msg"]) for error in exc.errors())
        raise ValueError(errors) from exc


def _extract_chat_message_content(response: Mapping[str, object]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ProviderRequestError("AI provider returned no chat choices.")

    first_choice = choices[0]
    if not isinstance(first_choice, Mapping):
        raise ProviderRequestError("AI provider returned an unexpected choice shape.")
    message = first_choice.get("message")
    if not isinstance(message, Mapping):
        raise ProviderRequestError("AI provider returned no assistant message.")

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ProviderRequestError("AI provider returned an empty assistant message.")
    return content


def _parse_provider_json(content: str) -> Mapping[str, object]:
    stripped = content.strip()
    if _looks_like_raw_code_output(stripped):
        raise ProviderRequestError("AI provider returned code-like text instead of structured JSON.")
    if not stripped.startswith("{"):
        raise ProviderRequestError("AI provider returned invalid strategy JSON.")
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise ProviderRequestError("AI provider returned invalid strategy JSON.") from exc
    if not isinstance(parsed, Mapping):
        raise ProviderRequestError("AI provider returned JSON that was not an object.")
    return cast(Mapping[str, object], parsed)


def _looks_like_raw_code_output(value: str) -> bool:
    lowered = value.lower()
    if lowered.startswith("```"):
        return True
    code_patterns = (
        r"^\s*(?:async\s+)?def\s+\w+\(",
        r"^\s*class\s+\w+[\(:]",
        r"^\s*import\s+\w+",
        r"^\s*from\s+\w+\s+import\s+",
        r"\b(?:eval|exec|subprocess|os\.system)\s*\(",
    )
    return any(re.search(pattern, value, re.IGNORECASE | re.MULTILINE) for pattern in code_patterns)


def _unsupported_terms_in_prompt(prompt: str) -> list[str]:
    lowered = prompt.lower()
    unsupported_terms = [term for term in FakeStrategyDraftProvider.unsupported_terms if term in lowered]
    if _contains_filesystem_path(prompt):
        unsupported_terms.append("filesystem path")
    return _unique_strings(unsupported_terms)


def _unsupported_prompt_draft(unsupported_terms: list[str]) -> StrategyDraft:
    return StrategyDraft(
        target_mode=TargetMode.UNSPECIFIED,
        strategy_kind=StrategyKind.UNSUPPORTED,
        assumptions=[],
        warnings=[
            "The request includes unsupported or unsafe concepts for the v1 builder.",
            "The builder returns inert data only and will not generate executable code.",
        ],
        unsupported=unsupported_terms,
        confidence=0.9,
        status=StrategyDraftStatus.UNSUPPORTED,
    )


def _safe_provider_error(exc: ProviderRequestError) -> str:
    message = str(exc)
    allowed_prefixes = (
        "AI provider returned",
        "AI provider rate limit",
        "AI provider request failed",
        "AI provider could not",
    )
    if message.startswith(allowed_prefixes):
        return message
    return "AI provider request failed."


def _extract_ticker(prompt: str) -> str | None:
    matches = re.findall(r"\b[A-Z]{1,5}\b", prompt)
    ignored = {"SMA", "ETF"}
    return next((match for match in matches if match not in ignored), None)


def _target_mode_from_prompt(prompt: str) -> TargetMode:
    lowered = prompt.lower()
    if "walk-forward" in lowered or "walk forward" in lowered or "out of sample" in lowered:
        return TargetMode.WALK_FORWARD
    if "grid search" in lowered or "optimize" in lowered or "optimise" in lowered:
        return TargetMode.GRID_SEARCH
    return TargetMode.SINGLE_RUN


def _has_rule_action(lowered_prompt: str, *actions: str) -> bool:
    action_pattern = "|".join(re.escape(action) for action in actions)
    return bool(re.search(rf"\b(?:{action_pattern})\b.{{0,40}}\bwhen\b", lowered_prompt))


def _contains_filesystem_path(prompt: str) -> bool:
    return bool(
        re.search(r"\b[A-Za-z]:\\", prompt)
        or re.search(r"(^|\s)/(?:tmp|var|etc|home|users)/", prompt, re.IGNORECASE)
        or "file://" in prompt.lower()
    )


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


def _close_indicator() -> IndicatorSpec:
    return IndicatorSpec(name=IndicatorName.CLOSE)


def _extract_single_indicator_window(prompt: str, indicator_label: str) -> int | None:
    escaped = re.escape(indicator_label)
    before_match = re.search(
        rf"\b(\d{{1,4}})\s*(?:day|-day)?\s+{escaped}\b",
        prompt,
        re.IGNORECASE,
    )
    if before_match is not None:
        return int(before_match.group(1))
    after_match = re.search(
        rf"\b{escaped}\s*(?:of\s+|window\s+)?(\d{{1,4}})\b",
        prompt,
        re.IGNORECASE,
    )
    if after_match is not None:
        return int(after_match.group(1))
    return None


def _extract_new_high_window(prompt: str) -> int | None:
    match = re.search(r"\b(\d{1,4})\s*(?:day|-day)?\s+(?:new\s+)?high\b", prompt, re.IGNORECASE)
    return int(match.group(1)) if match is not None else None


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
