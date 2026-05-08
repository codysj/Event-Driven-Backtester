"use client";

import { CheckCircle2, Circle, PlayCircle } from "lucide-react";
import type { ResearchGraphResponse, ResearchStep } from "../../lib/types";
import { stepLabel } from "./researchCopilotUtils";

const orderedSteps: ResearchStep[] = [
  "interpret_research_goal",
  "draft_strategy",
  "validate_draft",
  "compile_request",
  "await_user_approval",
  "run_workflow",
  "analyze_results",
  "recommend_next_step"
];

type ResearchStepTimelineProps = {
  state: ResearchGraphResponse | null;
};

export function ResearchStepTimeline({ state }: ResearchStepTimelineProps) {
  const completed = new Set(state?.steps ?? []);
  const current = state?.current_step ?? "interpret_research_goal";

  return (
    <section className="rounded-xl border border-lab-border bg-lab-surface p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-lab-text">Graph Timeline</h3>
        <span className="font-mono-finance text-xs text-lab-muted">{state?.session_id.slice(0, 8) ?? "no plan"}</span>
      </div>
      <div className="mt-4 grid gap-2 md:grid-cols-2 2xl:grid-cols-4">
        {orderedSteps.map((step) => {
          const isDone = completed.has(step);
          const isCurrent = current === step;
          const Icon = isDone ? CheckCircle2 : isCurrent ? PlayCircle : Circle;
          return (
            <div
              key={step}
              className={`flex min-h-16 items-center gap-3 rounded-lg border px-3 py-2 ${
                isDone
                  ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-100"
                  : isCurrent
                    ? "border-blue-500/30 bg-blue-500/10 text-blue-100"
                    : "border-lab-border bg-lab-bg text-lab-muted"
              }`}
            >
              <Icon size={16} className="shrink-0" />
              <span className="text-sm capitalize">{stepLabel(step)}</span>
            </div>
          );
        })}
      </div>
      {state?.audit_log.length ? (
        <div className="mt-4 space-y-2">
          {state.audit_log.slice(-4).map((event, index) => (
            <div key={`${event.step}-${index}`} className="rounded-lg border border-lab-border bg-lab-bg px-3 py-2 text-sm">
              <span className="font-mono-finance text-lab-muted">{stepLabel(event.step)}</span>
              <span className="ml-2 text-lab-secondary">{event.message}</span>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
