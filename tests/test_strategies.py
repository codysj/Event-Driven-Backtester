from __future__ import annotations

import pandas as pd
import pytest

from backtester.strategy import MeanReversionStrategy, MomentumStrategy, Signal, Strategy


def ohlcv_from_closes(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "volume": [100] * len(closes),
        },
        index=pd.date_range("2020-01-01", periods=len(closes), name="date"),
    )


def latest_signal(strategy: Strategy, data: pd.DataFrame) -> Signal:
    return strategy.generate_signal(data, current_index=len(data) - 1)


def slow_momentum_signal(data: pd.DataFrame, fast_window: int, slow_window: int) -> Signal:
    close = data["close"]
    if len(close) < slow_window + 1:
        return Signal.HOLD

    fast_now = float(close.iloc[-fast_window:].mean())
    fast_prev = float(close.iloc[-fast_window - 1 : -1].mean())
    slow_now = float(close.iloc[-slow_window:].mean())
    slow_prev = float(close.iloc[-slow_window - 1 : -1].mean())

    if fast_prev <= slow_prev and fast_now > slow_now:
        return Signal.BUY
    if fast_prev >= slow_prev and fast_now < slow_now:
        return Signal.SELL
    return Signal.HOLD


def slow_mean_reversion_signal(data: pd.DataFrame, window: int, num_std: float) -> Signal:
    close = data["close"]
    if len(close) < window:
        return Signal.HOLD

    latest_window = close.iloc[-window:]
    mean = float(latest_window.mean())
    std = float(latest_window.std())
    if std == 0.0:
        return Signal.HOLD

    current_price = float(close.iloc[-1])
    upper = mean + num_std * std
    lower = mean - num_std * std
    if current_price <= lower:
        return Signal.BUY
    if current_price >= upper:
        return Signal.SELL
    return Signal.HOLD


def test_momentum_is_strategy_subclass() -> None:
    strategy = MomentumStrategy()

    assert isinstance(strategy, Strategy)


def test_momentum_name() -> None:
    assert MomentumStrategy(fast_window=3, slow_window=5).name == "Momentum(3/5)"


def test_momentum_warmup_returns_hold() -> None:
    strategy = MomentumStrategy(fast_window=2, slow_window=3)

    assert latest_signal(strategy, ohlcv_from_closes([1.0, 2.0, 3.0])) is Signal.HOLD


def test_momentum_linear_uptrend_no_false_signal_after_warmup() -> None:
    strategy = MomentumStrategy(fast_window=2, slow_window=3)

    assert latest_signal(strategy, ohlcv_from_closes([1.0, 2.0, 3.0, 4.0])) is Signal.HOLD


def test_momentum_obvious_buy_crossover() -> None:
    strategy = MomentumStrategy(fast_window=2, slow_window=3)

    assert latest_signal(strategy, ohlcv_from_closes([5.0, 5.0, 5.0, 8.0])) is Signal.BUY


def test_momentum_obvious_sell_crossover() -> None:
    strategy = MomentumStrategy(fast_window=2, slow_window=3)

    assert latest_signal(strategy, ohlcv_from_closes([5.0, 5.0, 5.0, 2.0])) is Signal.SELL


def test_momentum_explicit_precompute_matches_lazy_signal() -> None:
    data = ohlcv_from_closes([5.0, 5.0, 5.0, 8.0])
    lazy_strategy = MomentumStrategy(fast_window=2, slow_window=3)
    precomputed_strategy = MomentumStrategy(fast_window=2, slow_window=3)

    precomputed_strategy.precompute(data)

    assert lazy_strategy.generate_signal(data, current_index=3) is Signal.BUY
    assert precomputed_strategy.generate_signal(data, current_index=3) is Signal.BUY


def test_momentum_invalid_windows() -> None:
    with pytest.raises(ValueError):
        MomentumStrategy(fast_window=0, slow_window=5)

    with pytest.raises(ValueError):
        MomentumStrategy(fast_window=3, slow_window=0)

    with pytest.raises(ValueError):
        MomentumStrategy(fast_window=5, slow_window=5)


def test_mean_reversion_is_strategy_subclass() -> None:
    strategy = MeanReversionStrategy()

    assert isinstance(strategy, Strategy)


def test_mean_reversion_name() -> None:
    assert MeanReversionStrategy(window=20, num_std=2.0).name == f"MeanReversion(20, 2.0{chr(963)})"


def test_mean_reversion_warmup_returns_hold() -> None:
    strategy = MeanReversionStrategy(window=3, num_std=1.0)

    assert latest_signal(strategy, ohlcv_from_closes([10.0, 11.0])) is Signal.HOLD


def test_mean_reversion_price_at_mean_returns_hold() -> None:
    strategy = MeanReversionStrategy(window=3, num_std=1.0)

    assert latest_signal(strategy, ohlcv_from_closes([9.0, 11.0, 10.0])) is Signal.HOLD


def test_mean_reversion_below_lower_band_returns_buy() -> None:
    strategy = MeanReversionStrategy(window=3, num_std=1.0)

    assert latest_signal(strategy, ohlcv_from_closes([10.0, 10.0, 0.0])) is Signal.BUY


def test_mean_reversion_above_upper_band_returns_sell() -> None:
    strategy = MeanReversionStrategy(window=3, num_std=1.0)

    assert latest_signal(strategy, ohlcv_from_closes([10.0, 10.0, 20.0])) is Signal.SELL


def test_mean_reversion_identical_prices_returns_hold() -> None:
    strategy = MeanReversionStrategy(window=3, num_std=1.0)

    assert latest_signal(strategy, ohlcv_from_closes([10.0, 10.0, 10.0])) is Signal.HOLD


def test_mean_reversion_explicit_precompute_matches_lazy_signal() -> None:
    data = ohlcv_from_closes([10.0, 10.0, 0.0])
    lazy_strategy = MeanReversionStrategy(window=3, num_std=1.0)
    precomputed_strategy = MeanReversionStrategy(window=3, num_std=1.0)

    precomputed_strategy.precompute(data)

    assert lazy_strategy.generate_signal(data, current_index=2) is Signal.BUY
    assert precomputed_strategy.generate_signal(data, current_index=2) is Signal.BUY


def test_mean_reversion_invalid_parameters() -> None:
    with pytest.raises(ValueError):
        MeanReversionStrategy(window=0, num_std=1.0)

    with pytest.raises(ValueError):
        MeanReversionStrategy(window=3, num_std=0.0)


def test_momentum_matches_sliced_reference_without_future_bars() -> None:
    closes = [10.0, 9.0, 8.0, 8.0, 11.0, 12.0, 10.0, 7.0, 6.0, 9.0]
    data = ohlcv_from_closes(closes)
    strategy = MomentumStrategy(fast_window=2, slow_window=3)
    strategy.precompute(data)

    actual = [strategy.generate_signal(data, current_index=i) for i in range(len(data))]
    expected = [slow_momentum_signal(data.iloc[: i + 1], 2, 3) for i in range(len(data))]

    assert actual == expected


def test_mean_reversion_matches_sliced_reference_without_future_bars() -> None:
    closes = [10.0, 10.0, 0.0, 10.0, 20.0, 10.0, 10.0, 5.0]
    data = ohlcv_from_closes(closes)
    strategy = MeanReversionStrategy(window=3, num_std=1.0)
    strategy.precompute(data)

    actual = [strategy.generate_signal(data, current_index=i) for i in range(len(data))]
    expected = [slow_mean_reversion_signal(data.iloc[: i + 1], 3, 1.0) for i in range(len(data))]

    assert actual == expected
