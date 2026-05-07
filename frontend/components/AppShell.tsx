import type { ReactNode } from "react";
import type { BacktestRequest, StrategyMetadata } from "../lib/types";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

type AppShellProps = {
  request: BacktestRequest;
  strategies: StrategyMetadata[];
  apiStatus: "checking" | "online" | "offline";
  isLoading: boolean;
  onRun: () => void;
  onReset: () => void;
  actionLabel?: string;
  configPanel: ReactNode;
  children: ReactNode;
};

export function AppShell({
  request,
  strategies,
  apiStatus,
  isLoading,
  onRun,
  onReset,
  actionLabel,
  configPanel,
  children
}: AppShellProps) {
  return (
    <main className="min-h-screen bg-lab-bg text-lab-text">
      <Sidebar />
      <TopBar
        request={request}
        strategies={strategies}
        status={apiStatus}
        isLoading={isLoading}
        onRun={onRun}
        onReset={onReset}
        actionLabel={actionLabel}
      />
      <div className="grid gap-5 px-4 py-5 lg:ml-[220px] xl:grid-cols-[minmax(0,1fr)_320px]">
        <section id="lab" className="min-w-0">
          {children}
        </section>
        <aside className="min-w-0 xl:sticky xl:top-[92px] xl:h-[calc(100vh-116px)] xl:overflow-y-auto">
          {configPanel}
        </aside>
      </div>
    </main>
  );
}
