from __future__ import annotations

from fastapi.testclient import TestClient

from backtester.api.main import app
from backtester.api.main import get_cors_origins
from backtester.api.schemas import (
    BacktestResponse,
    BacktestSeries,
    BacktestSummary,
    SeriesPoint,
)


client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_origins_default_to_local_frontend_ports(monkeypatch) -> None:
    monkeypatch.delenv("BACKTESTER_CORS_ORIGINS", raising=False)

    assert get_cors_origins() == ["http://localhost:3000", "http://127.0.0.1:3000"]


def test_cors_origins_can_be_configured_from_comma_separated_value() -> None:
    origins = get_cors_origins("http://localhost:3001, https://example.test, ")

    assert origins == ["http://localhost:3001", "https://example.test"]


def test_strategies_returns_supported_strategies() -> None:
    response = client.get("/api/strategies")

    assert response.status_code == 200
    strategy_ids = {strategy["id"] for strategy in response.json()["strategies"]}
    assert strategy_ids == {"momentum", "mean_reversion"}


def test_backtest_uses_service_layer(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def fake_run_backtest_from_request(request):  # type: ignore[no-untyped-def]
        return BacktestResponse(
            config={"ticker": request.ticker},
            summary=BacktestSummary(
                strategy_name="Momentum(10/50)",
                ticker=request.ticker,
                initial_value=100_000.0,
                final_value=101_000.0,
                total_return=0.01,
                annualized_return=0.1,
                sharpe_ratio=1.0,
                sortino_ratio=1.2,
                max_drawdown=-0.05,
                win_rate=0.5,
                profit_factor=1.3,
                total_trades=2,
            ),
            series=BacktestSeries(
                equity=[SeriesPoint(date="2020-01-01", value=100_000.0)],
                benchmark=[],
                drawdown=[SeriesPoint(date="2020-01-01", value=0.0)],
                price=[],
            ),
            trades=[],
        )

    monkeypatch.setattr("backtester.api.main.run_backtest_from_request", fake_run_backtest_from_request)

    response = client.post(
        "/api/backtest",
        json={
            "ticker": "aapl",
            "start_date": "2020-01-01",
            "end_date": "2021-01-01",
            "strategy": "momentum",
            "parameters": {"fast_window": 10, "slow_window": 50},
        },
    )

    assert response.status_code == 200
    assert response.json()["summary"]["ticker"] == "AAPL"


def test_invalid_strategy_returns_validation_error() -> None:
    response = client.post(
        "/api/backtest",
        json={
            "ticker": "AAPL",
            "start_date": "2020-01-01",
            "end_date": "2021-01-01",
            "strategy": "bad",
        },
    )

    assert response.status_code == 422
