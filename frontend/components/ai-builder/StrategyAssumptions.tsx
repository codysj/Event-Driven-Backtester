"use client";

type StrategyAssumptionsProps = {
  title: string;
  items: string[];
  tone?: "neutral" | "warning" | "danger";
};

export function StrategyAssumptions({ title, items, tone = "neutral" }: StrategyAssumptionsProps) {
  if (items.length === 0) {
    return null;
  }

  const toneClass =
    tone === "danger"
      ? "border-lab-red/40 bg-lab-red/10 text-red-100"
      : tone === "warning"
        ? "border-amber-500/30 bg-amber-500/10 text-amber-100"
        : "border-lab-border bg-lab-card text-lab-secondary";

  return (
    <section className={`rounded-xl border p-4 ${toneClass}`}>
      <h3 className="text-sm font-semibold text-lab-text">{title}</h3>
      <ul className="mt-2 space-y-1 text-sm leading-6">
        {items.map((item) => (
          <li key={item} className="break-words">
            {item}
          </li>
        ))}
      </ul>
    </section>
  );
}
