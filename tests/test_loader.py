from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from backtester.data.loader import DataLoader
from backtester.data.types import NoDataError, TickerNotFoundError


DownloadMock = Callable[..., pd.DataFrame]


def yahoo_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0],
            "High": [101.0, 102.0, 103.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [100.5, 101.5, 102.5],
            "Volume": [1_000, 1_100, 1_200],
        },
        index=pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]),
    )


def loader(tmp_path: Path) -> DataLoader:
    return DataLoader(cache_dir=tmp_path / ".backtester" / "cache")


def patch_download(monkeypatch: pytest.MonkeyPatch, frame: pd.DataFrame) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def fake_download(*args: Any, **kwargs: Any) -> pd.DataFrame:
        calls.append({"args": args, "kwargs": kwargs})
        return frame.copy()

    monkeypatch.setattr("backtester.data.loader.yf.download", fake_download)
    return calls


def test_known_ticker_returns_correct_schema(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    patch_download(monkeypatch, yahoo_frame())

    result = loader(tmp_path).fetch("aapl", "2020-01-01", "2020-01-10")

    assert not result.empty
    assert list(result.columns) == ["open", "high", "low", "close", "volume"]
    assert isinstance(result.index, pd.DatetimeIndex)
    assert result.index.name == "date"
    assert not result.isna().to_numpy().any()


def test_cache_file_created_after_first_fetch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    patch_download(monkeypatch, yahoo_frame())
    data_loader = loader(tmp_path)

    data_loader.fetch("aapl", "2020-01-01", "2020-01-10")

    expected = tmp_path / ".backtester" / "cache" / "AAPL_2020-01-01_2020-01-10.parquet"
    assert expected.exists()


def test_cache_hit_on_second_fetch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = patch_download(monkeypatch, yahoo_frame())
    data_loader = loader(tmp_path)

    first = data_loader.fetch("AAPL", "2020-01-01", "2020-01-10")
    second = data_loader.fetch("AAPL", "2020-01-01", "2020-01-10")

    assert len(calls) == 1
    pd.testing.assert_frame_equal(second, first)


def test_invalid_ticker_raises_ticker_not_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    patch_download(monkeypatch, pd.DataFrame())

    with pytest.raises(TickerNotFoundError):
        loader(tmp_path).fetch("not_a_real_ticker", "2020-01-01", "2020-01-10")


def test_empty_date_range_raises_no_data(tmp_path: Path) -> None:
    with pytest.raises(NoDataError):
        loader(tmp_path).fetch("AAPL", "2020-01-01", "2020-01-01")

    with pytest.raises(NoDataError):
        loader(tmp_path).fetch("AAPL", "2020-01-10", "2020-01-01")


def test_nan_values_removed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    frame = yahoo_frame()
    frame.loc[pd.Timestamp("2020-01-03"), "Close"] = pd.NA
    frame.loc[pd.Timestamp("2020-01-02"), "Open"] = pd.NA
    patch_download(monkeypatch, frame)

    result = loader(tmp_path).fetch("AAPL", "2020-01-01", "2020-01-10")

    assert not result.isna().to_numpy().any()
    assert list(result.index) == [pd.Timestamp("2020-01-03"), pd.Timestamp("2020-01-06")]


def test_extra_columns_removed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    frame = yahoo_frame()
    frame["Adj Close"] = [100.4, 101.4, 102.4]
    frame["Dividends"] = [0.0, 0.0, 0.0]
    patch_download(monkeypatch, frame)

    result = loader(tmp_path).fetch("AAPL", "2020-01-01", "2020-01-10")

    assert list(result.columns) == ["open", "high", "low", "close", "volume"]


def test_column_names_lowercased(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    patch_download(monkeypatch, yahoo_frame())

    result = loader(tmp_path).fetch("AAPL", "2020-01-01", "2020-01-10")

    assert list(result.columns) == ["open", "high", "low", "close", "volume"]

