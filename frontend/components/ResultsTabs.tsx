"use client";

import { useMemo, useState } from "react";
import type { BacktestResponse } from "../lib/types";
import { formatCurrency, formatDecimal, formatNumber, formatPercent } from "./formatters";
import { TradeTable } from "./TradeTable";

type ResultsTabsProps = {
  result: BacktestResponse;
};

type TabId = "summary" | "trades" | "metrics" | "parameters";

const tabs: { id: TabId; label: string }[] = [
  { id: "summary", label: "Summary" },
  { id: "trades", label: "Trades" },
  { id: "metrics", label: "Metrics" },
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
        {activeTab === "parameters" ? <KeyValueTable rows={configRows} /> : null}
      </div>
    </section>
  );
}
