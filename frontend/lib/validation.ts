import type { BacktestRequest, StrategyMetadata } from "./types";

export type FormErrors = Partial<Record<string, string>>;

export function validateBacktestRequest(request: BacktestRequest, strategy?: StrategyMetadata): FormErrors {
  const errors: FormErrors = {};

  if (!request.ticker.trim()) {
    errors.ticker = "Ticker is required.";
  }

  if (!request.start_date) {
    errors.start_date = "Start date is required.";
  }

  if (!request.end_date) {
    errors.end_date = "End date is required.";
  }

  if (request.start_date && request.end_date && request.start_date >= request.end_date) {
    errors.date_range = "Start date must be before end date.";
  }

  if (!Number.isFinite(request.initial_cash) || request.initial_cash <= 0) {
    errors.initial_cash = "Initial cash must be positive.";
  }

  if (!Number.isFinite(request.position_size_value) || request.position_size_value <= 0) {
    errors.position_size_value = "Size value must be positive.";
  }

  if (!Number.isFinite(request.commission_rate) || request.commission_rate < 0) {
    errors.commission_rate = "Commission must be zero or greater.";
  }

  if (!Number.isFinite(request.slippage_bps) || request.slippage_bps < 0) {
    errors.slippage_bps = "Slippage must be zero or greater.";
  }

  strategy?.parameters.forEach((parameter) => {
    const value = request.parameters[parameter.name];
    if (!Number.isFinite(value) || value <= 0) {
      errors[`parameters.${parameter.name}`] = `${parameter.label} must be positive.`;
    }
  });

  if (request.strategy === "momentum") {
    const fast = request.parameters.fast_window;
    const slow = request.parameters.slow_window;
    if (Number.isFinite(fast) && Number.isFinite(slow) && fast >= slow) {
      errors["parameters.fast_window"] = "Fast window must be less than slow window.";
      errors["parameters.slow_window"] = "Slow window must be greater than fast window.";
    }
  }

  return errors;
}

export function hasErrors(errors: FormErrors): boolean {
  return Object.keys(errors).length > 0;
}
