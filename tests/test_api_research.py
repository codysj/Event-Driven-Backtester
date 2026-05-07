from __future__ import annotations

from dataclasses import dataclass
import math

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backtester.api.main import app
from backtester.api.schemas import GridSearchRequest, WalkForwardRequest
from backtester.api.services import (
    run_grid_search_from_request,
    run_walk_forward_from_request,
)
from backtester.data.loader import DataLoader


client = TestClient(app)


@dataclass
class FakeLoader(DataLoader):
    data: pd.DataFrame

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        del ticker
        sliced = self.data.loc[pd.Timestamp(start) : pd.Timestamp(end)]
        if sliced.empty:
            return self.data.copy()
        return sliced.copy()


def make_research_data(periods: int = 180) -> pd.DataFrame:
    closes = [
        100.0 + index * 0.15 + math.sin(index / 3) * 4.0 + math.sin(index / 11) * 2.5
        for index in range(periods)
    ]
    return pd.DataFrame(
        {
            "open": closes,
            "high": [price * 1.01 for price in closes],
            "low": [price * 0.99 for price in closes],
            "close": closes,
            "volume": [1000] * len(closes),
        },
        index=pd.date_range("2020-01-01", periods=len(closes), name="date"),
    )


def momentum_grid_request(**overrides: object) -> GridSearchRequest:
    payload: dict[str, object] = {
        "ticker": "aapl",
        "start_date": "2020-01-01",
        "end_date": "2020-06-01",
        "strategy": "momentum",
        "parameter_grid": {"fast_window": [2, 3], "slow_window": [6, 8]},
        "optimization_metric": "total_return",
        "benchmark": True,
        "max_results": 10,
    }
    payload.update(overrides)
    return GridSearchRequest.model_validate(payload)


def walk_forward_request(**overrides: object) -> WalkForwardRequest:
    payload: dict[str, object] = {
        "ticker": "AAPL",
        "start_date": "2020-01-01",
        "end_date": "2020-06-20",
        "strategy": "momentum",
        "parameter_grid": {"fast_window": [2, 3], "slow_window": [6, 8]},
        "optimization_metric": "total_return",
        "benchmark": False,
        "train_window_bars": 50,
        "test_window_bars": 20,
        "step_bars": 20,
    }
    payload.update(overrides)
    return WalkForwardRequest.model_validate(payload)


def test_grid_search_service_returns_ranked_heatmap_and_best(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("backtester.api.services.DataLoader", lambda: FakeLoader(make_research_data()))

    response = run_grid_search_from_request(momentum_grid_request())

    assert response.config["ticker"] == "AAPL"
    assert response.total_combinations == 4
    assert len(response.results) == 4
    assert response.best_parameters is not None
    assert response.best_row is not None
    assert response.results[0].total_return is not None
    assert len(response.heatmap) == 4
    assert response.heatmap[0].x_param == "fast_window"
    assert response.analysis.robustness_score >= 0


def test_grid_search_invalid_parameter_range_rejected() -> None:
    response = client.post(
        "/api/grid-search",
        json={
            "ticker": "AAPL",
            "start_date": "2020-01-01",
            "end_date": "2020-06-01",
            "strategy": "momentum",
            "parameter_grid": {"fast_window": [], "slow_window": [8]},
        },
    )

    assert response.status_code == 422


def test_grid_search_unsupported_strategy_rejected() -> None:
    response = client.post(
        "/api/grid-search",
        json={
            "ticker": "AAPL",
            "start_date": "2020-01-01",
            "end_date": "2020-06-01",
            "strategy": "unsupported",
            "parameter_grid": {"fast_window": [2], "slow_window": [8]},
        },
    )

    assert response.status_code == 422


def test_grid_search_failed_combination_is_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("backtester.api.services.DataLoader", lambda: FakeLoader(make_research_data()))

    request = momentum_grid_request(parameter_grid={"fast_window": [2, 10], "slow_window": [8]})
    response = run_grid_search_from_request(request)

    assert response.total_combinations == 2
    assert len(response.failed_combinations) == 1
    assert response.failed_combinations[0].error is not None
    assert "fast_window" in response.failed_combinations[0].parameters


def test_grid_search_results_are_sorted_by_selected_metric(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("backtester.api.services.DataLoader", lambda: FakeLoader(make_research_data()))

    response = run_grid_search_from_request(momentum_grid_request(optimization_metric="sharpe_ratio"))
    values = [row.sharpe_ratio for row in response.results if row.error is None and row.sharpe_ratio is not None]

    assert values == sorted(values, reverse=True)


def test_walk_forward_generates_folds_and_out_of_sample_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("backtester.api.services.DataLoader", lambda: FakeLoader(make_research_data()))

    response = run_walk_forward_from_request(walk_forward_request())

    assert response.summary.number_of_folds == len(response.folds)
    assert response.summary.number_of_folds >= 2
    assert response.summary.average_train_metric is not None
    assert response.summary.average_test_metric is not None
    first_fold = response.folds[0]
    assert first_fold.selected_parameters["fast_window"] in [2, 3]
    assert first_fold.test_start > first_fold.train_end
    assert first_fold.test_metrics is not None


def test_walk_forward_invalid_windows_rejected() -> None:
    response = client.post(
        "/api/walk-forward",
        json={
            "ticker": "AAPL",
            "start_date": "2020-01-01",
            "end_date": "2020-06-01",
            "strategy": "momentum",
            "parameter_grid": {"fast_window": [2], "slow_window": [8]},
            "train_window_bars": 20,
            "test_window_bars": 20,
            "step_bars": 10,
        },
    )

    assert response.status_code == 422
