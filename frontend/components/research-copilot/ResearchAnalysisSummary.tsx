"use client";

import { Lightbulb, ListChecks } from "lucide-react";
import type { JsonValue, ResearchGraphResponse } from "../../lib/types";
import { formatCurrency, formatDecimal, formatNumber, formatPercent } from "../formatters";
import { modeLabel } from "./researchCopilotUtils";

type ResearchAnalysisSummaryProps = {
  state: ResearchGraphResponse | null;
};

function formatSummaryValue(value: JsonValue): string {
  if (value === null) return "n/a";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") {
    if (Math.abs(value) < 1 && value !== 0) return formatPercent(value);
    if (Math.abs(value) > 1000) return formatCurrency(value);
    return formatDecimal(value);
  }
  if (typeof value === "string") return value.replaceAll("_", " ");
  if (Array.isArray(value)) return value.map(formatSummaryValue).join(", ");
  return JSON.stringify(value);
}

export function ResearchAnalysisSummary({ state }: ResearchAnalysisSummaryProps) {
  const result = state?.workflow_result ?? null;
  const summaryEntries = Object.entries(result?.summary ?? {});

  return (
    <section className="rounded-xl border border-lab-border bg-lab-surface p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-lab-border bg-lab-card text-lab-cyan">
          <Lightbulb size={18} />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-lab-text">Analysis And Next Step</h3>
          <p className="mt-2 text-sm leading-6 text-lab-secondary">
            Deterministic heuristics from the backend, shown as research notes rather than predictions.
          </p>
        </div>
      </div>

      {result ? (
        <div className="mt-4 grid gap-3 md:grid-cols-2 2xl:grid-cols-4">
          <div className="rounded-lg border border-lab-border bg-lab-bg p-3">
            <div className="text-xs uppercase tracking-[0.16em] text-lab-muted">Workflow</div>
            <div className="mt-1 font-mono-finance text-sm text-lab-text">{modeLabel(result.target_mode)}</div>
          </div>
          {summaryEntries.map(([key, value]) => (
            <div key={key} className="rounded-lg border border-lab-border bg-lab-bg p-3">
              <div className="text-xs uppercase tracking-[0.16em] text-lab-muted">{key.replaceAll("_", " ")}</div>
              <div className="mt-1 break-words font-mono-finance text-sm text-lab-text">
                {typeof value === "number" && key.includes("combinations") ? formatNumber(value) : formatSummaryValue(value)}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-4 rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm text-lab-secondary">
          Run an approved workflow to receive result analysis.
        </p>
      )}

      {state?.analysis.length ? (
        <div className="mt-4 rounded-lg border border-lab-border bg-lab-bg p-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-lab-text">
            <ListChecks size={15} />
            Backend Analysis
          </div>
          <ul className="mt-2 space-y-1 text-sm leading-6 text-lab-secondary">
            {state.analysis.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {state?.recommendation ? (
        <div className="mt-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm leading-6 text-emerald-100">
          {state.recommendation}
        </div>
      ) : null}
    </section>
  );
}
