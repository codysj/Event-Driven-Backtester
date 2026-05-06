import type { BacktestResponse } from "../lib/types";
import { DrawdownChart } from "./DrawdownChart";
import { EquityChart } from "./EquityChart";
import { formatCurrency, formatDecimal, formatPercent } from "./formatters";
import { MetricCard } from "./MetricCard";
import { TradeTable } from "./TradeTable";

type ResultsDashboardProps = {
  result: BacktestResponse | null;
};

function toneFor(value: number): "positive" | "negative" | "neutral" {
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}

export function ResultsDashboard({ result }: ResultsDashboardProps) {
  if (!result) {
    return (
      <div className="flex min-h-[520px] items-center justify-center rounded-lg border border-dashed border-slate-700 bg-slate-900/40 p-10 text-center">
        <div>
          <p className="text-xl font-semibold text-slate-100">Choose a ticker, strategy, and date range.</p>
          <p className="mt-3 max-w-xl text-slate-400">
            Backtest Lab runs a historical simulation through the Python engine, then shows portfolio value, risk, benchmark comparison, drawdown, and trade history.
          </p>
        </div>
      </div>
    );
  }

  const summary = result.summary;
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Final Value" value={formatCurrency(summary.final_value)} helper={summary.strategy_name} tone={toneFor(summary.final_value - summary.initial_value)} />
        <MetricCard label="Total Return" value={formatPercent(summary.total_return)} tone={toneFor(summary.total_return)} />
        <MetricCard label="Sharpe Ratio" value={formatDecimal(summary.sharpe_ratio)} />
        <MetricCard label="Max Drawdown" value={formatPercent(summary.max_drawdown)} tone="negative" />
        <MetricCard label="Alpha" value={formatPercent(summary.alpha ?? 0)} helper={summary.alpha === null ? "No benchmark" : undefined} tone={toneFor(summary.alpha ?? 0)} />
        <MetricCard label="Beta" value={formatDecimal(summary.beta)} />
        <MetricCard label="Info Ratio" value={formatDecimal(summary.information_ratio)} />
        <MetricCard label="Trades" value={String(summary.total_trades)} helper={`Win rate ${formatPercent(summary.win_rate)}`} />
      </div>
      <EquityChart equity={result.series.equity} benchmark={result.series.benchmark} />
      <DrawdownChart drawdown={result.series.drawdown} />
      <TradeTable trades={result.trades} />
    </div>
  );
}

