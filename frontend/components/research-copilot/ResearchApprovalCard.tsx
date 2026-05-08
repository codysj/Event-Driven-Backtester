"use client";

import { Play, ShieldCheck } from "lucide-react";
import type { ApprovedAction, ResearchGraphResponse } from "../../lib/types";
import { actionForTarget, actionLabel, modeLabel } from "./researchCopilotUtils";

type ResearchApprovalCardProps = {
  state: ResearchGraphResponse | null;
  isApproving: boolean;
  onApprove: (action: ApprovedAction) => void;
};

export function ResearchApprovalCard({ state, isApproving, onApprove }: ResearchApprovalCardProps) {
  const requiredAction = actionForTarget(state?.target_mode);
  const canApprove = Boolean(state?.approval_required && state.compile_payload && requiredAction && state.validation_errors.length === 0);

  return (
    <section className="rounded-xl border border-lab-border bg-lab-surface p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-lab-border bg-lab-card text-lab-green">
          <ShieldCheck size={18} />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-lab-text">Approval Gate</h3>
          <p className="mt-2 text-sm leading-6 text-lab-secondary">
            Planning stops here until you explicitly approve one {modeLabel(state?.target_mode)} workflow run.
          </p>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-blue-500/30 bg-blue-500/10 p-3 text-sm leading-6 text-blue-100">
        No broker connection, no live trading, no generated Python execution. Approval runs only the compiled existing API workflow.
      </div>

      <button
        type="button"
        disabled={!canApprove || isApproving || requiredAction === null}
        onClick={() => {
          if (requiredAction) onApprove(requiredAction);
        }}
        className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-lab-blue px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
      >
        <Play size={16} />
        {isApproving ? "Running approved workflow..." : actionLabel(requiredAction)}
      </button>

      {!canApprove ? (
        <p className="mt-3 text-xs leading-5 text-lab-muted">
          A ready compiled payload with no validation errors is required before approval is enabled.
        </p>
      ) : null}
    </section>
  );
}
