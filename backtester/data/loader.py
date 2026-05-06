"""OHLCV data loading, caching, cleaning, and validation."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import re

import pandas as pd
import yfinance as yf

from backtester.data.types import NoDataError, TickerNotFoundError


EXPECTED_COLUMNS: list[str] = ["open", "high", "low", "close", "volume"]
YFINANCE_COLUMN_MAP: dict[str, str] = {
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
}
VALID_TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


class DataLoader:
    """Fetch, cache, clean, validate, and return OHLCV market data."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._cache_dir = cache_dir if cache_dir is not None else Path.home() / ".backtester" / "cache"

    def fetch(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        """Return cleaned OHLCV bars for ``ticker`` over ``[start, end)``."""
        normalized_ticker = self._normalize_ticker(ticker)
        self._validate_date_range(start, end)

        cache_path = self._cache_path(normalized_ticker, start, end)
        if cache_path.exists():
            try:
                cached = self._load_from_cache(cache_path)
                self._validate_schema(cached)
                return cached
            except (OSError, ValueError, TypeError, ImportError):
                pass

        raw = self._download(normalized_ticker, start, end)
        if raw.empty:
            self._raise_empty_data_error(normalized_ticker)

        cleaned = self._clean_yfinance_data(raw)
        if cleaned.empty:
            self._raise_empty_data_error(normalized_ticker)

        self._validate_schema(cleaned)
        self._save_to_cache(cleaned, cache_path)
        return cleaned

    def _cache_path(self, ticker: str, start: str, end: str) -> Path:
        return self._cache_dir / f"{ticker}_{start}_{end}.parquet"

    def _load_from_cache(self, path: Path) -> pd.DataFrame:
        return pd.read_parquet(path)

    def _save_to_cache(self, df: pd.DataFrame, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path)

    def _download(self, ticker: str, start: str, end: str) -> pd.DataFrame:
        raw = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False)
        if not isinstance(raw, pd.DataFrame):
            msg = "yfinance returned a non-DataFrame response."
            raise NoDataError(msg)
        return raw

    def _clean_yfinance_data(self, raw: pd.DataFrame) -> pd.DataFrame:
        df = self._flatten_columns(raw.copy())
        df = df.rename(columns={column: str(column).strip().lower() for column in df.columns})
        df = df.rename(columns=YFINANCE_COLUMN_MAP)

        missing_columns = [column for column in EXPECTED_COLUMNS if column not in df.columns]
        if missing_columns:
            msg = f"Missing required OHLCV columns: {missing_columns}"
            raise NoDataError(msg)

        cleaned = df.loc[:, EXPECTED_COLUMNS].copy()
        cleaned.index = pd.to_datetime(cleaned.index)
        cleaned.index.name = "date"
        cleaned = cleaned.sort_index()

        for column in EXPECTED_COLUMNS:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

        # Forward-fill handles occasional missing market data fields; remaining
        # rows are dropped because downstream strategy logic requires complete
        # OHLCV bars.
        cleaned = cleaned.ffill().dropna()
        volume_values = pd.to_numeric(cleaned["volume"], errors="coerce")
        if volume_values.isna().any() or not (volume_values % 1 == 0).all():
            msg = "volume column must contain integer-compatible values."
            raise ValueError(msg)
        cleaned["volume"] = cleaned["volume"].astype("int64")
        return cleaned

    def _validate_schema(self, df: pd.DataFrame) -> None:
        if df.empty:
            msg = "DataFrame contains no OHLCV rows."
            raise NoDataError(msg)

        if list(df.columns) != EXPECTED_COLUMNS:
            msg = f"Expected columns {EXPECTED_COLUMNS}, got {list(df.columns)}."
            raise ValueError(msg)

        if not isinstance(df.index, pd.DatetimeIndex):
            msg = "DataFrame index must be a DatetimeIndex."
            raise ValueError(msg)

        if df.index.name != "date":
            msg = 'DataFrame index name must be "date".'
            raise ValueError(msg)

        if df.isna().to_numpy().any():
            msg = "DataFrame must not contain NaN values."
            raise ValueError(msg)

        for column in ["open", "high", "low", "close"]:
            if not pd.api.types.is_numeric_dtype(df[column]):
                msg = f"{column} column must be numeric."
                raise ValueError(msg)

        if not pd.api.types.is_numeric_dtype(df["volume"]):
            msg = "volume column must be numeric."
            raise ValueError(msg)

        volume_values = pd.to_numeric(df["volume"], errors="coerce")
        if volume_values.isna().any() or not (volume_values % 1 == 0).all():
            msg = "volume column must contain integer-compatible values."
            raise ValueError(msg)

    def _flatten_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(df.columns, pd.MultiIndex):
            return df

        for level in range(df.columns.nlevels):
            values = [str(value).strip().lower() for value in df.columns.get_level_values(level)]
            if {"open", "high", "low", "close", "volume"}.issubset(set(values)):
                flattened = df.copy()
                flattened.columns = df.columns.get_level_values(level)
                return flattened

        flattened = df.copy()
        flattened.columns = [
            "_".join(str(part) for part in column if str(part))
            for column in df.columns.to_flat_index()
        ]
        return flattened

    def _validate_date_range(self, start: str, end: str) -> None:
        try:
            start_date = date.fromisoformat(start)
            end_date = date.fromisoformat(end)
        except ValueError as exc:
            msg = "start and end must use YYYY-MM-DD format."
            raise NoDataError(msg) from exc

        if start_date >= end_date:
            msg = "start must be earlier than end."
            raise NoDataError(msg)

    def _normalize_ticker(self, ticker: str) -> str:
        normalized = ticker.strip().upper()
        if not normalized:
            msg = "ticker must not be empty."
            raise TickerNotFoundError(msg)
        return normalized

    def _raise_empty_data_error(self, ticker: str) -> None:
        if not VALID_TICKER_PATTERN.fullmatch(ticker):
            msg = f"Ticker appears invalid: {ticker}"
            raise TickerNotFoundError(msg)

        msg = f"No OHLCV data returned for {ticker} in the requested date range."
        raise NoDataError(msg)
