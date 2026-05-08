"use client";

import { Braces, ClipboardList } from "lucide-react";
import type { ResearchGraphResponse, StrategyCompileResponse } from "../../lib/types";
import { formatNumber } from "../formatters";
import { modeLabel } from "./researchCopilotUtils";

type ResearchPayloadPreviewProps = {
  state: ResearchGraphResponse | null;
  onLoadCompiled: (response: StrategyCompileResponse) => void;
};

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-lab-border bg-lab-bg p-3">
      <div className="text-xs uppercase tracking-[0.16em] text-lab-muted">{label}</div>
      <div className="mt-1 break-words font-mono-finance text-sm text-lab-text">{value}</div>
    </div>
  );
}

function parameterLabel(values: Record<string, number> | null | undefined): string {
  if (!values || Object.keys(values).length === 0) return "Not specified";
  return Object.entries(values)
    .map(([key, value]) => `${key.replaceAll("_", " ")} ${formatNumber(value)}`)
    .join(" / ");
}

function parameterGridLabel(values: Record<string, number[]> | null | undefined): string {
  if (!values || Object.keys(values).length === 0) return "Not specified";
  return Object.entries(values)
    .map(([key, items]) => `${key.replaceAll("_", " ")} [${items.join(", ")}]`)
    .join(" / ");
}

export function ResearchPayloadPreview({ state, onLoadCompiled }: ResearchPayloadPreviewProps) {
  const draft = state?.draft ?? null;
  const compileResponse = state?.compile_response ?? null;
  const compilePayload = state?.compile_payload ?? null;
  const canLoad = compileResponse?.status === "ready" && compilePayload !== null && state?.target_mode !== "unspecified";

  return (
    <section className="rounded-xl border border-lab-border bg-lab-surface p-5">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <h3 className="text-sm font-semibold text-lab-text">Draft And Payload</h3>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-lab-secondary">
            The compiled payload is inert JSON for an existing Backtest Lab workflow.
          </p>
        </div>
        <button
          type="button"
          disabled={!canLoad || !compileResponse}
          onClick={() => {
            if (compileResponse && canLoad) onLoadCompiled(compileResponse);
          }}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-lab-border bg-lab-card px-3 py-2 text-sm font-semibold text-lab-secondary transition hover:border-lab-blue hover:text-lab-text disabled:cursor-not-allowed disabled:opacity-50"
          title={canLoad ? "Load the compiled request into its existing workflow form" : "A ready compiled payload is required first"}
        >
          <ClipboardList size={15} />
          Load into form
        </button>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2 2xl:grid-cols-4">
        <Detail label="Target Mode" value={modeLabel(state?.target_mode)} />
        <Detail label="Ticker / Dates" value={`${draft?.ticker ?? "Ticker needed"} / ${draft?.start_date ?? "default start"} to ${draft?.end_date ?? "default end"}`} />
        <Detail label="Strategy" value={(draft?.strategy_kind ?? "not specified").replaceAll("_", " ")} />
        <Detail label="Status" value={state?.status.replaceAll("_", " ") ?? "No plan"} />
        <Detail label="Parameters" value={parameterLabel(draft?.parameters)} />
        <Detail label="Parameter Grid" value={parameterGridLabel(draft?.parameter_grid)} />
        <Detail label="Metric" value={draft?.optimization_metric?.replaceAll("_", " ") ?? "Not specified"} />
        <Detail label="Approval Required" value={state?.approval_required ? "Yes" : "No"} />
      </div>

      <details className="mt-4 rounded-lg border border-lab-border bg-lab-bg p-3">
        <summary className="flex cursor-pointer items-center gap-2 text-sm font-semibold text-lab-text">
          <Braces size={15} />
          Compiled Payload JSON
        </summary>
        <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-words font-mono-finance text-xs leading-5 text-lab-secondary">
          {JSON.stringify(compilePayload ?? compileResponse?.payload ?? null, null, 2)}
        </pre>
      </details>
    </section>
  );
}
