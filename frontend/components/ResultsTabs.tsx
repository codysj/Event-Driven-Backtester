"use client";

import { useMemo, useState } from "react";
import type { BacktestResponse } from "../lib/types";
import { exportBacktestMetricsJson, exportBacktestTradesCsv, exportConfigJson } from "../lib/exports";
import { formatCurrency, formatDecimal, formatNumber, formatPercent } from "./formatters";
import { TradeTable } from "./TradeTable";

type ResultsTabsProps = {
  result: BacktestResponse;
};

type TabId = "summary" | "trades" | "metrics" | "risk" | "parameters";

const tabs: { id: TabId; label: string }[] = [
  { id: "summary", label: "Summary" },
  { id: "trades", label: "Trades" },
  { id: "metrics", label: "Metrics" },
  { id: "risk", label: "Risk" },
  { id: "parameters", label: "Parameters" }
];

function KeyValueTable({ rows }: { rows: { label: string; value: string; helper?: string }[] }) {
  return (
    <div className="overflow-hidden rounded-xl border border-lab-border bg-lab-surface">
      <table className="min-w-full text-sm">
        <tbody className="divide-y divide-lab-border/70">
          {rows.map((row) => (
            <tr key={row.label} className="align-top">
              <td className="w-56 px-4 py-3 text-lab-secondary">{row.label}</td>
              <td className="px-4 py-3">
                <div className="font-mono-finance text-lab-text">{row.value}</div>
                {row.helper ? <div className="mt-1 text-xs text-lab-muted">{row.helper}</div> : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function stringifyConfigValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "n/a";
  }
  if (typeof value === "number") {
    return formatNumber(value);
  }
  if (typeof value === "boolean") {
    return value ? "Enabled" : "Disabled";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

export function ResultsTabs({ result }: ResultsTabsProps) {
  const [activeTab, setActiveTab] = useState<TabId>("summary");
  const summary = result.summary;

  const metricsRows = [
    { label: "Total Return", value: formatPercent(summary.total_return), helper: "Return from initial to final portfolio value." },
    { label: "Annualized Return", value: formatPercent(summary.annualized_return), helper: "Return normalized to one year." },
    { label: "Sharpe Ratio", value: formatDecimal(summary.sharpe_ratio), helper: "Risk-adjusted return using total volatility." },
    { label: "Sortino Ratio", value: formatDecimal(summary.sortino_ratio), helper: "Risk-adjusted return using downside volatility." },
    { label: "Max Drawdown", value: formatPercent(summary.max_drawdown), helper: "Largest peak-to-trough decline." },
    { label: "Win Rate", value: formatPercent(summary.win_rate), helper: "Share of closed trades that were profitable." },
    { label: "Profit Factor", value: formatDecimal(summary.profit_factor), helper: "Gross profits divided by gross losses." },
    { label: "Alpha", value: summary.alpha === null ? "n/a" : formatPercent(summary.alpha), helper: "Benchmark-relative annualized excess return." },
    { label: "Beta", value: formatDecimal(summary.beta), helper: "Sensitivity to the benchmark series." },
    {
      label: "Information Ratio",
      value: formatDecimal(summary.information_ratio),
      helper: "Benchmark-relative return per unit of tracking error."
    }
  ];

  const configRows = useMemo(() => {
    const baseRows = Object.entries(result.config)
      .filter(([key]) => key !== "parameters")
      .map(([key, value]) => ({
        label: key.replaceAll("_", " "),
        value: stringifyConfigValue(value)
      }));

    const parameters = result.config.parameters;
    if (parameters && typeof parameters === "object" && !Array.isArray(parameters)) {
      Object.entries(parameters as Record<string, unknown>).forEach(([key, value]) => {
        baseRows.push({
          label: `parameter: ${key.replaceAll("_", " ")}`,
          value: stringifyConfigValue(value)
        });
      });
    }

    return baseRows;
  }, [result.config]);

  const riskRows = result.risk
    ? [
        { label: "Best Day", value: formatPercent(result.risk.best_day), helper: "Best daily portfolio return." },
        { label: "Worst Day", value: formatPercent(result.risk.worst_day), helper: "Worst daily portfolio return." },
        { label: "Drawdown Duration", value: `${result.risk.drawdown_duration_days} bars`, helper: "Longest stretch below a prior high." },
        { label: "VaR 95", value: formatPercent(result.risk.value_at_risk_95), helper: "Historical 5th percentile daily return." },
        { label: "CVaR 95", value: formatPercent(result.risk.conditional_value_at_risk_95), helper: "Average daily return beyond VaR." }
      ]
    : [];

  return (
    <section className="rounded-xl border border-lab-border bg-lab-card p-3">
      <div className="flex flex-wrap gap-2 border-b border-lab-border pb-3">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
              activeTab === tab.id ? "bg-lab-blue text-white" : "text-lab-secondary hover:bg-lab-surface hover:text-lab-text"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="pt-4">
        {activeTab === "summary" ? (
          <div className="rounded-xl border border-lab-border bg-lab-surface p-5">
            <h3 className="text-base font-semibold text-lab-text">Run Interpretation</h3>
            <p className="mt-3 max-w-4xl text-sm leading-7 text-lab-secondary">
              The strategy ended at <span className="font-mono-finance text-lab-text">{formatCurrency(summary.final_value)}</span> from{" "}
              <span className="font-mono-finance text-lab-text">{formatCurrency(summary.initial_value)}</span>, with a max drawdown of{" "}
              <span className="font-mono-finance text-lab-text">{formatPercent(summary.max_drawdown)}</span> and{" "}
              <span className="font-mono-finance text-lab-text">{summary.total_trades}</span> executed trades. This is a historical simulation for research context only.
            </p>
          </div>
        ) : null}

        {activeTab === "trades" ? <TradeTable trades={result.trades} /> : null}
        {activeTab === "metrics" ? <KeyValueTable rows={metricsRows} /> : null}
        {activeTab === "risk" ? (
          <div className="space-y-4">
            <KeyValueTable rows={riskRows} />
            <div className="overflow-hidden rounded-xl border border-lab-border bg-lab-surface">
              <div className="border-b border-lab-border px-4 py-3">
                <h3 className="text-sm font-semibold text-lab-text">Monthly Returns</h3>
              </div>
              <div className="max-h-[320px] overflow-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="sticky top-0 z-10 border-b border-lab-border bg-lab-card text-xs uppercase tracking-[0.16em] text-lab-muted">
                    <tr>
                      <th className="px-4 py-3 font-medium">Year</th>
                      <th className="px-4 py-3 font-medium">Month</th>
                      <th className="px-4 py-3 text-right font-medium">Return</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-lab-border/70">
                    {(result.risk?.monthly_returns ?? []).map((row) => (
                      <tr key={`${row.year}-${row.month}`} className="bg-lab-surface">
                        <td className="px-4 py-3 font-mono-finance text-lab-secondary">{row.year}</td>
                        <td className="px-4 py-3 font-mono-finance text-lab-secondary">{row.month}</td>
                        <td className="px-4 py-3 text-right font-mono-finance text-lab-text">{formatPercent(row.return)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : null}
        {activeTab === "parameters" ? <KeyValueTable rows={configRows} /> : null}
      </div>

      <div className="mt-4 flex flex-wrap gap-2 border-t border-lab-border pt-3">
        <button
          type="button"
          onClick={() => exportBacktestTradesCsv(result)}
          className="rounded-lg border border-lab-border bg-lab-surface px-3 py-2 text-sm text-lab-secondary transition hover:border-lab-blue hover:text-lab-text"
        >
          Trades CSV
        </button>
        <button
          type="button"
          onClick={() => exportBacktestMetricsJson(result)}
          className="rounded-lg border border-lab-border bg-lab-surface px-3 py-2 text-sm text-lab-secondary transition hover:border-lab-blue hover:text-lab-text"
        >
          Metrics JSON
        </button>
        <button
          type="button"
          onClick={() => exportConfigJson(result.config)}
          className="rounded-lg border border-lab-border bg-lab-surface px-3 py-2 text-sm text-lab-secondary transition hover:border-lab-blue hover:text-lab-text"
        >
          Config JSON
        </button>
      </div>
    </section>
  );
}
