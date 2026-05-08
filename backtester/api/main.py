"""FastAPI app for Backtest Lab."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from backtester.ai import compile_strategy_draft, draft_strategy_from_request
from backtester.ai.schemas import (
    StrategyCompileRequest,
    StrategyCompileResponse,
    StrategyDraftRequest,
    StrategyDraftResponse,
)
from backtester.api.schemas import (
    BacktestRequest,
    BacktestResponse,
    GridSearchRequest,
    GridSearchResponse,
    HealthResponse,
    StrategiesResponse,
    WalkForwardRequest,
    WalkForwardResponse,
)
from backtester.api.services import (
    available_strategies,
    run_backtest_from_request,
    run_grid_search_from_request,
    run_walk_forward_from_request,
)


logger = logging.getLogger("uvicorn.error")
DEFAULT_CORS_ORIGINS = ("http://localhost:3000", "http://127.0.0.1:3000")
DEFAULT_AI_PROVIDER = "fake"
DEFAULT_OPENROUTER_MODEL = "tencent/hy3-preview:free"
DEFAULT_AI_MODELS = {
    "openrouter": DEFAULT_OPENROUTER_MODEL,
    "deepseek": "deepseek-chat",
    "openai_compatible": "gpt-4o-mini",
}


def get_cors_origins(raw_origins: str | None = None) -> list[str]:
    """Return configured CORS origins for the local API."""
    value = os.getenv("BACKTESTER_CORS_ORIGINS") if raw_origins is None else raw_origins
    if value is None or value.strip() == "":
        return list(DEFAULT_CORS_ORIGINS)

    origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    return origins if origins else list(DEFAULT_CORS_ORIGINS)


app = FastAPI(title="Backtest Lab API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def log_backend_configuration() -> None:
    """Log non-sensitive backend configuration useful for local startup checks."""
    provider = _selected_ai_provider()
    logger.info("AI provider selected: %s", provider)
    logger.info("AI model: %s", _selected_ai_model(provider))


app.router.add_event_handler("startup", log_backend_configuration)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return API health status."""
    return HealthResponse(status="ok")


@app.get("/api/strategies", response_model=StrategiesResponse)
def strategies() -> StrategiesResponse:
    """Return strategy metadata for the frontend form."""
    return StrategiesResponse(strategies=available_strategies())


@app.post("/api/ai/strategy-draft", response_model=StrategyDraftResponse)
def draft_ai_strategy(request: StrategyDraftRequest) -> StrategyDraftResponse:
    """Create an inert strategy draft from a natural-language prompt."""
    return draft_strategy_from_request(request)


@app.post("/api/ai/compile", response_model=StrategyCompileResponse)
def compile_ai_strategy(request: StrategyCompileRequest) -> StrategyCompileResponse:
    """Compile an inert strategy draft into an existing API request payload."""
    return compile_strategy_draft(request.draft)


@app.post("/api/backtest", response_model=BacktestResponse)
def run_backtest(request: BacktestRequest) -> BacktestResponse:
    """Run a backtest from a validated request body."""
    try:
        return run_backtest_from_request(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        detail = f"Could not run backtest for {request.ticker} between {request.start_date} and {request.end_date}."
        raise HTTPException(status_code=500, detail=detail) from exc


@app.post("/api/grid-search", response_model=GridSearchResponse)
def run_grid_search(request: GridSearchRequest) -> GridSearchResponse:
    """Run a parameter grid search from a validated request body."""
    try:
        return run_grid_search_from_request(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        detail = f"Could not run grid search for {request.ticker} between {request.start_date} and {request.end_date}."
        raise HTTPException(status_code=500, detail=detail) from exc


@app.post("/api/walk-forward", response_model=WalkForwardResponse)
def run_walk_forward(request: WalkForwardRequest) -> WalkForwardResponse:
    """Run walk-forward validation from a validated request body."""
    try:
        return run_walk_forward_from_request(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        detail = f"Could not run walk-forward validation for {request.ticker} between {request.start_date} and {request.end_date}."
        raise HTTPException(status_code=500, detail=detail) from exc


def _selected_ai_provider() -> str:
    configured = os.getenv("BACKTESTER_AI_PROVIDER")
    if configured is None or configured.strip() == "":
        return DEFAULT_AI_PROVIDER
    return configured.strip().lower()


def _selected_ai_model(provider: str) -> str:
    configured = os.getenv("BACKTESTER_AI_MODEL")
    if configured is not None and configured.strip():
        return configured.strip()
    return DEFAULT_AI_MODELS.get(provider, "default")
