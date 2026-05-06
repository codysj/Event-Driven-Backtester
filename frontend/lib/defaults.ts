import type { BacktestRequest, StrategyMetadata } from "./types";

export const DEFAULT_BACKTEST_REQUEST: BacktestRequest = {
  ticker: "AAPL",
  start_date: "2018-01-01",
  end_date: "2023-12-31",
  strategy: "momentum",
  initial_cash: 100000,
  commission_rate: 0.001,
  slippage_bps: 5,
  position_size_method: "FIXED_DOLLAR",
  position_size_value: 10000,
  benchmark: true,
  parameters: {
    fast_window: 10,
    slow_window: 50
  }
};

export const FALLBACK_STRATEGIES: StrategyMetadata[] = [
  {
    id: "momentum",
    name: "Momentum SMA Crossover",
    description: "Uses fast and slow moving average crossovers to generate buy/sell signals.",
    parameters: [
      { name: "fast_window", type: "integer", default: 10, min: 1, label: "Fast Window" },
      { name: "slow_window", type: "integer", default: 50, min: 2, label: "Slow Window" }
    ]
  },
  {
    id: "mean_reversion",
    name: "Mean Reversion",
    description: "Uses Bollinger-style bands to identify overextended prices.",
    parameters: [
      { name: "window", type: "integer", default: 20, min: 1, label: "Window" },
      { name: "num_std", type: "number", default: 2, min: 0.1, label: "Standard Deviations" }
    ]
  }
];
