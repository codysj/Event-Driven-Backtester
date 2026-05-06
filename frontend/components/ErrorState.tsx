import { AlertTriangle, Terminal } from "lucide-react";

type ErrorStateProps = {
  message: string;
};

export function ErrorState({ message }: ErrorStateProps) {
  return (
    <div className="rounded-xl border border-red-500/30 bg-red-950/20 p-4">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-500/10 text-lab-red">
          <AlertTriangle size={18} />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-red-100">Backtest failed</h3>
          <p className="mt-1 text-sm leading-6 text-red-100/80">{message}</p>
          <p className="mt-3 text-sm leading-6 text-lab-secondary">
            Possible causes include the FastAPI server not running, yfinance/network access being unavailable, or the requested market data not being cached.
          </p>
          <div className="mt-3 inline-flex max-w-full items-center gap-2 overflow-x-auto rounded-lg border border-red-500/25 bg-lab-bg px-3 py-2">
            <Terminal size={15} className="shrink-0 text-lab-red" />
            <code className="font-mono-finance text-xs text-red-100">python -m uvicorn backtester.api.main:app --reload</code>
          </div>
        </div>
      </div>
    </div>
  );
}
