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


def test_momentum_is_strategy_subclass() -> None:
    strategy = MomentumStrategy()

    assert isinstance(strategy, Strategy)


def test_momentum_name() -> None:
    assert MomentumStrategy(fast_window=3, slow_window=5).name == "Momentum(3/5)"


def test_momentum_warmup_returns_hold() -> None:
    strategy = MomentumStrategy(fast_window=2, slow_window=3)

    assert strategy.generate_signal(ohlcv_from_closes([1.0, 2.0, 3.0])) is Signal.HOLD


def test_momentum_linear_uptrend_no_false_signal_after_warmup() -> None:
    strategy = MomentumStrategy(fast_window=2, slow_window=3)

    assert strategy.generate_signal(ohlcv_from_closes([1.0, 2.0, 3.0, 4.0])) is Signal.HOLD


def test_momentum_obvious_buy_crossover() -> None:
    strategy = MomentumStrategy(fast_window=2, slow_window=3)

    assert strategy.generate_signal(ohlcv_from_closes([5.0, 5.0, 5.0, 8.0])) is Signal.BUY


def test_momentum_obvious_sell_crossover() -> None:
    strategy = MomentumStrategy(fast_window=2, slow_window=3)

    assert strategy.generate_signal(ohlcv_from_closes([5.0, 5.0, 5.0, 2.0])) is Signal.SELL


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
    assert MeanReversionStrategy(window=20, num_std=2.0).name == "MeanReversion(20, 2.0σ)"


def test_mean_reversion_warmup_returns_hold() -> None:
    strategy = MeanReversionStrategy(window=3, num_std=1.0)

    assert strategy.generate_signal(ohlcv_from_closes([10.0, 11.0])) is Signal.HOLD


def test_mean_reversion_price_at_mean_returns_hold() -> None:
    strategy = MeanReversionStrategy(window=3, num_std=1.0)

    assert strategy.generate_signal(ohlcv_from_closes([9.0, 11.0, 10.0])) is Signal.HOLD


def test_mean_reversion_below_lower_band_returns_buy() -> None:
    strategy = MeanReversionStrategy(window=3, num_std=1.0)

    assert strategy.generate_signal(ohlcv_from_closes([10.0, 10.0, 0.0])) is Signal.BUY


def test_mean_reversion_above_upper_band_returns_sell() -> None:
    strategy = MeanReversionStrategy(window=3, num_std=1.0)

    assert strategy.generate_signal(ohlcv_from_closes([10.0, 10.0, 20.0])) is Signal.SELL


def test_mean_reversion_identical_prices_returns_hold() -> None:
    strategy = MeanReversionStrategy(window=3, num_std=1.0)

    assert strategy.generate_signal(ohlcv_from_closes([10.0, 10.0, 10.0])) is Signal.HOLD


def test_mean_reversion_invalid_parameters() -> None:
    with pytest.raises(ValueError):
        MeanReversionStrategy(window=0, num_std=1.0)

    with pytest.raises(ValueError):
        MeanReversionStrategy(window=3, num_std=0.0)
