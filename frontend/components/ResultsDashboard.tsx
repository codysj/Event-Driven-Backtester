import type { BacktestRequest, BacktestResponse, StrategyMetadata } from "../lib/types";
import { DrawdownChart } from "./DrawdownChart";
import { EmptyState } from "./EmptyState";
import { EquityChart } from "./EquityChart";
import { ErrorState } from "./ErrorState";
import { formatCurrency, formatDate, formatDecimal, formatPercent } from "./formatters";
import { LoadingSkeleton } from "./LoadingSkeleton";
import { MetricCard } from "./MetricCard";
import { ResultsTabs } from "./ResultsTabs";

type ResultsDashboardProps = {
  result: BacktestResponse | null;
  request: BacktestRequest;
  strategies: StrategyMetadata[];
  isLoading: boolean;
  error: string | null;
  onRunDefault: () => void;
};

function toneFor(value: number | null | undefined): "positive" | "negative" | "neutral" {
  if (value === null || value === undefined) return "neutral";
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}

function RunHero({
  result,
  request,
  strategies,
  status
}: {
  result: BacktestResponse | null;
  request: BacktestRequest;
  strategies: StrategyMetadata[];
  status: "Ready" | "Running" | "Complete" | "Error";
}) {
  const summary = result?.summary;
  const strategyName = result?.summary.strategy_name ?? strategies.find((strategy) => strategy.id === request.strategy)?.name ?? request.strategy;
  const ticker = result?.summary.ticker ?? (request.ticker || "AAPL");
  const title = `${ticker} ${strategyName}`;
  const statusClass =
    status === "Complete"
      ? "border-emerald-500/30 bg-emerald-500/10 text-lab-green"
      : status === "Error"
        ? "border-red-500/30 bg-red-500/10 text-lab-red"
        : status === "Running"
          ? "border-blue-500/30 bg-blue-500/10 text-lab-cyan"
          : "border-lab-border bg-lab-card text-lab-secondary";

  return (
    <section id="overview" className="rounded-xl border border-lab-border bg-lab-surface p-5 shadow-[0_24px_80px_rgba(0,0,0,0.24)]">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-xl font-semibold text-lab-text">{title}</h2>
            <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusClass}`}>{status}</span>
          </div>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-lab-secondary">
            {formatDate(request.start_date)} to {formatDate(request.end_date)} with {formatCurrency(request.initial_cash)} initial cash
            {request.benchmark ? " and buy-and-hold benchmark enabled." : "."}
          </p>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-lab-secondary">
            Run event-driven strategy simulations with realistic costs and benchmark-aware analytics.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:min-w-[360px]">
          <div className="rounded-lg border border-lab-border bg-lab-card p-3">
            <div className="text-xs text-lab-muted">Ticker</div>
            <div className="mt-1 font-mono-finance text-sm text-lab-text">{summary?.ticker ?? request.ticker}</div>
          </div>
          <div className="rounded-lg border border-lab-border bg-lab-card p-3">
            <div className="text-xs text-lab-muted">Benchmark</div>
            <div className="mt-1 font-mono-finance text-sm text-lab-text">{request.benchmark ? "Enabled" : "Off"}</div>
          </div>
          <div className="rounded-lg border border-lab-border bg-lab-card p-3">
            <div className="text-xs text-lab-muted">Trades</div>
            <div className="mt-1 font-mono-finance text-sm text-lab-text">{summary?.total_trades ?? 0}</div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function ResultsDashboard({
  result,
  request,
  strategies,
  isLoading,
  error,
  onRunDefault
}: ResultsDashboardProps) {
  const status = isLoading ? "Running" : error ? "Error" : result ? "Complete" : "Ready";

  if (isLoading && !result) {
    return (
      <div className="space-y-5">
        <RunHero result={result} request={request} strategies={strategies} status={status} />
        <LoadingSkeleton />
      </div>
    );
  }

  if (!result) {
    return (
      <div className="space-y-5">
        <RunHero result={result} request={request} strategies={strategies} status={status} />
        {error ? <ErrorState message={error} /> : null}
        <EmptyState onRunDefault={onRunDefault} isLoading={isLoading} />
      </div>
    );
  }

  const summary = result.summary;

  return (
    <div className="space-y-5">
      <RunHero result={result} request={request} strategies={strategies} status={status} />
      {error ? <ErrorState message={error} /> : null}

      <div className="grid gap-3 md:grid-cols-2 2xl:grid-cols-4">
        <MetricCard label="Total Return" value={formatPercent(summary.total_return)} helper="portfolio growth" tone={toneFor(summary.total_return)} />
        <MetricCard label="Annualized Return" value={formatPercent(summary.annualized_return)} helper="yearly compounded rate" tone={toneFor(summary.annualized_return)} />
        <MetricCard label="Sharpe" value={formatDecimal(summary.sharpe_ratio)} helper="risk-adjusted return" tone={toneFor(summary.sharpe_ratio)} />
        <MetricCard label="Sortino" value={formatDecimal(summary.sortino_ratio)} helper="downside risk adjusted" tone={toneFor(summary.sortino_ratio)} />
        <MetricCard label="Max Drawdown" value={formatPercent(summary.max_drawdown)} helper="largest equity decline" tone="negative" />
        <MetricCard label="Final Value" value={formatCurrency(summary.final_value)} helper="ending portfolio value" tone={toneFor(summary.final_value - summary.initial_value)} />
        <MetricCard label="Total Trades" value={String(summary.total_trades)} helper="executed orders" />
        <MetricCard label="Win Rate" value={formatPercent(summary.win_rate)} helper={`profit factor ${formatDecimal(summary.profit_factor)}`} tone={toneFor(summary.win_rate - 0.5)} />
      </div>

      <EquityChart equity={result.series.equity} benchmark={result.series.benchmark} />
      <DrawdownChart drawdown={result.series.drawdown} />
      <ResultsTabs result={result} />
    </div>
  );
}
