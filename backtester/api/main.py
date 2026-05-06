"""FastAPI app for Backtest Lab."""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backtester.api.schemas import BacktestRequest, BacktestResponse, HealthResponse, StrategiesResponse
from backtester.api.services import available_strategies, run_backtest_from_request


DEFAULT_CORS_ORIGINS = ("http://localhost:3000", "http://127.0.0.1:3000")


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


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return API health status."""
    return HealthResponse(status="ok")


@app.get("/api/strategies", response_model=StrategiesResponse)
def strategies() -> StrategiesResponse:
    """Return strategy metadata for the frontend form."""
    return StrategiesResponse(strategies=available_strategies())


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
