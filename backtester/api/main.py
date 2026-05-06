"""FastAPI app for Backtest Lab."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backtester.api.schemas import BacktestRequest, BacktestResponse, HealthResponse, StrategiesResponse
from backtester.api.services import available_strategies, run_backtest_from_request


app = FastAPI(title="Backtest Lab API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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

