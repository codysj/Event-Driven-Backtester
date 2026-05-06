import { BarChart3, BookOpen, FlaskConical, Grid3X3, LineChart, ShieldCheck } from "lucide-react";

const navItems = [
  { label: "Overview", icon: BarChart3, href: "#overview", enabled: true },
  { label: "Backtest Lab", icon: FlaskConical, href: "#lab", enabled: true },
  { label: "Grid Search", icon: Grid3X3, href: "#parameters", enabled: false },
  { label: "Trades", icon: LineChart, href: "#trades", enabled: true },
  { label: "Docs", icon: BookOpen, href: "#docs", enabled: true }
];

export function Sidebar() {
  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-lab-border bg-lab-surface/95 px-4 py-4 lg:fixed lg:inset-y-0 lg:left-0 lg:w-[220px] lg:border-b-0 lg:border-r">
      <div className="rounded-xl border border-lab-border bg-lab-card p-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-lab-blue text-white shadow-lg shadow-blue-950/40">
          <FlaskConical size={20} />
        </div>
        <h1 className="mt-4 text-lg font-semibold text-lab-text">Backtest Lab</h1>
        <p className="mt-1 text-xs leading-5 text-lab-secondary">Event-driven strategy research.</p>
      </div>

      <nav className="mt-5 flex gap-2 overflow-x-auto lg:flex-col lg:overflow-visible">
        {navItems.map((item) => {
          const Icon = item.icon;
          return item.enabled ? (
            <a
              key={item.label}
              href={item.href}
              className="flex min-w-max items-center gap-3 rounded-lg px-3 py-2 text-sm text-lab-secondary transition hover:bg-lab-card hover:text-lab-text"
            >
              <Icon size={16} />
              {item.label}
            </a>
          ) : (
            <div
              key={item.label}
              className="flex min-w-max items-center justify-between gap-3 rounded-lg px-3 py-2 text-sm text-lab-muted opacity-70"
              aria-disabled="true"
            >
              <span className="flex items-center gap-3">
                <Icon size={16} />
                {item.label}
              </span>
              <span className="hidden rounded-full border border-lab-border px-2 py-0.5 text-[10px] uppercase tracking-wide lg:inline">
                Soon
              </span>
            </div>
          );
        })}
      </nav>

      <div className="mt-5 hidden flex-1 lg:block" />

      <div className="mt-5 rounded-xl border border-lab-border bg-lab-bg p-3">
        <div className="flex items-center gap-2 text-xs font-medium text-lab-text">
          <ShieldCheck size={15} className="text-lab-green" />
          Built from scratch
        </div>
        <p className="mt-2 text-xs leading-5 text-lab-secondary">No backtesting libraries</p>
      </div>
    </aside>
  );
}
