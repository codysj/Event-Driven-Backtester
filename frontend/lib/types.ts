export type StrategyId = "momentum" | "mean_reversion";

export type PositionSizeMethod =
  | "FIXED_DOLLAR"
  | "FIXED_QUANTITY"
  | "ALL_IN"
  | "PERCENT_EQUITY"
  | "VOLATILITY_TARGET";

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
  position_size_method: PositionSizeMethod;
  position_size_value: number;
  benchmark: boolean;
  parameters: Record<string, number>;
};

export type OptimizationMetric =
  | "total_return"
  | "annualized_return"
  | "sharpe_ratio"
  | "sortino_ratio"
  | "max_drawdown"
  | "information_ratio"
  | "profit_factor"
  | "win_rate";

export type ParameterGrid = Record<string, number[]>;

export type ResearchBaseRequest = Omit<BacktestRequest, "parameters"> & {
  parameter_grid: ParameterGrid;
  optimization_metric: OptimizationMetric;
};

export type GridSearchRequest = ResearchBaseRequest & {
  max_results: number;
};

export type WalkForwardRequest = ResearchBaseRequest & {
  train_window_bars: number;
  test_window_bars: number;
  step_bars: number;
};

export type HealthResponse = {
  status: string;
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
  risk: RiskAnalytics | null;
};

export type RiskAnalytics = {
  best_day: number;
  worst_day: number;
  drawdown_duration_days: number;
  value_at_risk_95: number;
  conditional_value_at_risk_95: number;
  rolling_sharpe: SeriesPoint[];
  rolling_volatility: SeriesPoint[];
  rolling_drawdown: SeriesPoint[];
  monthly_returns: { year: number; month: number; return: number }[];
};

export type GridSearchRow = {
  rank: number | null;
  parameters: Record<string, number>;
  final_value: number | null;
  total_return: number | null;
  annualized_return: number | null;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  max_drawdown: number | null;
  information_ratio: number | null;
  benchmark_total_return: number | null;
  excess_total_return: number | null;
  profit_factor: number | null;
  win_rate: number | null;
  total_trades: number;
  error: string | null;
};

export type HeatmapPoint = {
  x_param: string;
  y_param: string;
  x: number;
  y: number;
  value: number | null;
  parameters: Record<string, number>;
};

export type RobustnessAnalysis = {
  robustness_score: number;
  warnings: string[];
  notes: string[];
  nearby_parameter_stability: number | null;
  trade_count_flags: string[];
  drawdown_flags: string[];
  overfit_risk_flags: string[];
};

export type GridSearchResponse = {
  config: Record<string, unknown>;
  strategy_id: StrategyId;
  strategy_name: string;
  optimization_metric: OptimizationMetric;
  total_combinations: number;
  results: GridSearchRow[];
  failed_combinations: GridSearchRow[];
  best_parameters: Record<string, number> | null;
  best_row: GridSearchRow | null;
  heatmap: HeatmapPoint[];
  analysis: RobustnessAnalysis;
};

export type WalkForwardFold = {
  fold: number;
  train_start: string;
  train_end: string;
  test_start: string;
  test_end: string;
  selected_parameters: Record<string, number>;
  train_metrics: GridSearchRow | null;
  test_metrics: GridSearchRow | null;
  degradation_ratio: number | null;
  warnings: string[];
};

export type WalkForwardSummary = {
  average_train_metric: number | null;
  average_test_metric: number | null;
  average_degradation: number | null;
  number_of_folds: number;
  parameter_stability: number | null;
  warnings: string[];
};

export type WalkForwardResponse = {
  config: Record<string, unknown>;
  strategy_id: StrategyId;
  strategy_name: string;
  optimization_metric: OptimizationMetric;
  folds: WalkForwardFold[];
  summary: WalkForwardSummary;
};
