"use client";

import { Activity, Github } from "lucide-react";
import { useEffect, useState } from "react";
import { BacktestForm } from "../components/BacktestForm";
import { ResultsDashboard } from "../components/ResultsDashboard";
import { fetchStrategies, runBacktest } from "../lib/api";
import type { BacktestRequest, BacktestResponse, StrategyMetadata } from "../lib/types";

const fallbackStrategies: StrategyMetadata[] = [
  {
    id: "momentum",
    name: "Momentum SMA Crossover",
    description: "Uses fast and slow moving average crossovers to generate buy/sell signals.",
    parameters: [
      { name: "fast_window", type: "integer", default: 10, min: 1, label: "Fast Window" },
      { name: "slow_window", type: "integer", default: 50, min: 2, label: "Slow Window" }
    ]
  },
  {
    id: "mean_reversion",
    name: "Mean Reversion",
    description: "Uses Bollinger-style bands to identify overextended prices.",
    parameters: [
      { name: "window", type: "integer", default: 20, min: 1, label: "Window" },
      { name: "num_std", type: "number", default: 2, min: 0.1, label: "Standard Deviations" }
    ]
  }
];

export default function HomePage() {
  const [strategies, setStrategies] = useState<StrategyMetadata[]>(fallbackStrategies);
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStrategies()
      .then(setStrategies)
      .catch(() => setStrategies(fallbackStrategies));
  }, []);

  async function handleSubmit(request: BacktestRequest) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await runBacktest(request);
      setResult(response);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not run the backtest.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950">
      <header className="border-b border-slate-800 bg-slate-950/95 px-6 py-5">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-400 text-slate-950">
              <Activity size={22} />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-100">Backtest Lab</h1>
              <p className="text-sm text-slate-400">Strategy research dashboard powered by a Python backtesting engine</p>
            </div>
          </div>
          <a href="#" className="hidden items-center gap-2 rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-slate-500 md:flex">
            <Github size={16} />
            GitHub
          </a>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[360px_1fr]">
        <aside className="rounded-lg border border-slate-800 bg-slate-900/70 p-5">
          <div className="mb-5">
            <h2 className="text-lg font-semibold text-slate-100">Backtest Controls</h2>
            <p className="mt-1 text-sm text-slate-400">Configure a historical simulation. This is research only, not live trading.</p>
          </div>
          <BacktestForm strategies={strategies} isLoading={isLoading} onSubmit={handleSubmit} />
        </aside>

        <section>
          {error ? (
            <div className="mb-4 rounded-lg border border-rose-900 bg-rose-950/40 p-4 text-sm text-rose-200">
              {error}
            </div>
          ) : null}
          {isLoading ? (
            <div className="mb-4 rounded-lg border border-sky-900 bg-sky-950/40 p-4 text-sm text-sky-200">
              Running simulation and preparing results...
            </div>
          ) : null}
          <ResultsDashboard result={result} />
        </section>
      </div>
    </main>
  );
}
