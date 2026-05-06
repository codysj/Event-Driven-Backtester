# Benchmark Results

Benchmarks are intentionally reproducible and do not require network access by default.

Run the synthetic benchmark:

```bash
python benchmarks/benchmark_backtest.py
```

Run a DataLoader/yfinance benchmark:

```bash
python benchmarks/benchmark_backtest.py --real --ticker AAPL --start 2010-01-01 --end 2024-01-01
```

Run the profiler:

```bash
python benchmarks/profile_backtest.py
```

## Results

The original sliced-DataFrame baseline must be measured from a pre-Stage-7 commit or reconstructed branch. The current optimized implementation uses full DataFrame access with `current_index`, precomputed strategy indicators, and NumPy close-price access in the engine loop.

Measured locally on Windows with Python 3.14.0, synthetic 2,500-bar OHLCV data, `MomentumStrategy(10/50)`, zero commission, and zero slippage:

| Version | Time | Throughput | Speedup |
|---------|------|------------|---------|
| Baseline sliced DataFrame | TODO: measure from pre-optimization commit | TODO | 1.0x |
| Precomputed indicators + NumPy hot loop | 0.008092 s | 308,943.29 bars/sec | TODO: compare to baseline |

Latest cProfile synthetic run:

- Total calls: 55,313
- Total time: 0.017 s
- Top cumulative function: `BacktestEngine.run`
- Main hot-loop strategy cost: `MomentumStrategy.generate_signal`
