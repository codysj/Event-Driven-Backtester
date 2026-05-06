export type StrategyId = "momentum" | "mean_reversion";

export type StrategyParameter = {
  name: string;
  type: "integer" | "number";
  default: number;
  min: number;
  label: string;
};

export type StrategyMetadata = {
  id: StrategyId;
  name: string;
  description: string;
  parameters: StrategyParameter[];
};

export type BacktestRequest = {
  ticker: string;
  start_date: string;
  end_date: string;
  strategy: StrategyId;
  initial_cash: number;
  commission_rate: number;
  slippage_bps: number;
  position_size_method: string;
  position_size_value: number;
  benchmark: boolean;
  parameters: Record<string, number>;
};

export type BacktestSummary = {
  strategy_name: string;
  ticker: string;
  initial_value: number;
  final_value: number;
  total_return: number;
  annualized_return: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  alpha: number | null;
  beta: number | null;
  information_ratio: number | null;
  total_trades: number;
};

export type SeriesPoint = {
  date: string;
  value: number;
};

export type PricePoint = {
  date: string;
  close: number;
};

export type Trade = {
  ticker: string;
  side: "BUY" | "SELL";
  quantity: number;
  price: number;
  commission: number;
  timestamp: string;
};

export type BacktestResponse = {
  config: Record<string, unknown>;
  summary: BacktestSummary;
  series: {
    equity: SeriesPoint[];
    benchmark: SeriesPoint[];
    drawdown: SeriesPoint[];
    price: PricePoint[];
  };
  trades: Trade[];
};

