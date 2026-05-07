"use client";

import { Activity, BookOpen, Github, Play, RotateCcw } from "lucide-react";
import type { BacktestRequest, StrategyMetadata } from "../lib/types";
import { formatCurrency, formatDate } from "./formatters";

type ApiStatus = "checking" | "online" | "offline";

type TopBarProps = {
  request: BacktestRequest;
  strategies: StrategyMetadata[];
  status: ApiStatus;
  isLoading: boolean;
  onRun: () => void;
  onReset: () => void;
  actionLabel?: string;
};

function StatusIndicator({ status }: { status: ApiStatus }) {
  const label = status === "online" ? "API connected" : status === "offline" ? "API not reached" : "Checking API";
  const dotClass = status === "online" ? "bg-lab-green" : status === "offline" ? "bg-lab-amber" : "bg-lab-muted";

  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-lab-border bg-lab-card px-3 py-1 text-xs text-lab-secondary">
      <span className={`h-2 w-2 rounded-full ${dotClass}`} />
      {label}
    </span>
  );
}

export function TopBar({ request, strategies, status, isLoading, onRun, onReset, actionLabel = "Run Backtest" }: TopBarProps) {
  const strategyName = strategies.find((strategy) => strategy.id === request.strategy)?.name ?? request.strategy;

  return (
    <header className="sticky top-0 z-30 border-b border-lab-border bg-lab-bg/90 px-4 py-3 backdrop-blur lg:ml-[220px]">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <StatusIndicator status={status} />
            <span className="inline-flex items-center gap-2 rounded-full border border-lab-border bg-lab-card px-3 py-1 text-xs text-lab-secondary">
              <Activity size={13} className="text-lab-cyan" />
              Research tool only. Not investment advice.
            </span>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
            <span className="font-mono-finance font-semibold text-lab-text">{request.ticker || "Ticker"}</span>
            <span className="text-lab-muted">/</span>
            <span className="text-lab-secondary">{strategyName}</span>
            <span className="text-lab-muted">/</span>
            <span className="font-mono-finance text-lab-secondary">
              {formatDate(request.start_date)} to {formatDate(request.end_date)}
            </span>
            <span className="text-lab-muted">/</span>
            <span className="font-mono-finance text-lab-secondary">{formatCurrency(request.initial_cash)}</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <a
            href="https://github.com/codysj/Event-Driven-Backtester"
            className="inline-flex items-center gap-2 rounded-lg border border-lab-border bg-lab-card px-3 py-2 text-sm text-lab-secondary transition hover:border-lab-blue hover:text-lab-text"
          >
            <Github size={15} />
            GitHub
          </a>
          <a
            href="#docs"
            className="inline-flex items-center gap-2 rounded-lg border border-lab-border bg-lab-card px-3 py-2 text-sm text-lab-secondary transition hover:border-lab-blue hover:text-lab-text"
          >
            <BookOpen size={15} />
            Docs
          </a>
          <button
            type="button"
            onClick={onReset}
            disabled={isLoading}
            className="inline-flex items-center gap-2 rounded-lg border border-lab-border bg-lab-card px-3 py-2 text-sm text-lab-secondary transition hover:border-lab-blue hover:text-lab-text disabled:cursor-not-allowed disabled:opacity-60"
          >
            <RotateCcw size={15} />
            Reset defaults
          </button>
          <button
            type="button"
            onClick={onRun}
            disabled={isLoading}
            className="inline-flex items-center gap-2 rounded-lg bg-lab-blue px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-950/40 transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Play size={15} />
            {isLoading ? "Running..." : actionLabel}
          </button>
        </div>
      </div>
    </header>
  );
}
