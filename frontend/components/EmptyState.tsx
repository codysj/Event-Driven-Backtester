import { Play, Sparkles } from "lucide-react";

type EmptyStateProps = {
  onRunDefault: () => void;
  isLoading: boolean;
};

export function EmptyState({ onRunDefault, isLoading }: EmptyStateProps) {
  return (
    <div className="flex min-h-[560px] items-center justify-center rounded-xl border border-dashed border-lab-border bg-lab-surface/70 p-8 text-center">
      <div className="max-w-2xl">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-lab-border bg-lab-card text-lab-cyan">
          <Sparkles size={22} />
        </div>
        <h2 className="mt-5 text-2xl font-semibold text-lab-text">Backtest Lab</h2>
        <p className="mt-3 text-sm leading-7 text-lab-secondary">
          Run event-driven strategy simulations with realistic costs and benchmark-aware analytics.
        </p>
        <button
          type="button"
          onClick={onRunDefault}
          disabled={isLoading}
          className="mt-6 inline-flex items-center justify-center gap-2 rounded-lg bg-lab-blue px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-950/40 transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Play size={16} />
          Run default AAPL backtest
        </button>
        <div className="mt-6 grid gap-3 text-left sm:grid-cols-3">
          {["Equity vs benchmark", "Drawdown profile", "Trades and parameters"].map((item) => (
            <div key={item} className="rounded-xl border border-lab-border bg-lab-card p-3 text-xs text-lab-secondary">
              {item}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
