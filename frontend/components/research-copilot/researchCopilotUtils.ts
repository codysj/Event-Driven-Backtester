import type { AiTargetMode, ApprovedAction, ResearchStep } from "../../lib/types";

export function modeLabel(mode: AiTargetMode | null | undefined): string {
  if (mode === "single_run") return "Single Run";
  if (mode === "grid_search") return "Grid Search";
  if (mode === "walk_forward") return "Walk-Forward";
  return "Unspecified";
}

export function actionForTarget(mode: AiTargetMode | null | undefined): ApprovedAction | null {
  if (mode === "single_run") return "run_backtest";
  if (mode === "grid_search") return "run_grid_search";
  if (mode === "walk_forward") return "run_walk_forward";
  return null;
}

export function actionLabel(action: ApprovedAction | null): string {
  if (action === "run_backtest") return "Approve and run backtest";
  if (action === "run_grid_search") return "Approve and run grid search";
  if (action === "run_walk_forward") return "Approve and run walk-forward";
  return "Approval unavailable";
}

export function stepLabel(step: ResearchStep): string {
  return step.replaceAll("_", " ");
}

export function statusTone(status: string): string {
  if (status === "completed") return "border-emerald-500/30 bg-emerald-500/10 text-emerald-100";
  if (status === "awaiting_approval") return "border-blue-500/30 bg-blue-500/10 text-blue-100";
  if (status === "blocked") return "border-lab-red/40 bg-lab-red/10 text-red-100";
  return "border-lab-border bg-lab-card text-lab-secondary";
}
