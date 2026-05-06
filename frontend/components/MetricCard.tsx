type MetricCardProps = {
  label: string;
  value: string;
  helper?: string;
  tone?: "positive" | "negative" | "neutral";
  eyebrow?: string;
};

const toneClasses = {
  positive: "text-lab-green",
  negative: "text-lab-red",
  neutral: "text-lab-text"
};

export function MetricCard({ label, value, helper, tone = "neutral", eyebrow }: MetricCardProps) {
  return (
    <div className="min-h-[116px] rounded-xl border border-lab-border bg-lab-card p-4 shadow-[0_18px_50px_rgba(0,0,0,0.18)]">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm font-medium text-lab-secondary">{label}</div>
        {eyebrow ? <div className="font-mono-finance text-[11px] uppercase tracking-wide text-lab-muted">{eyebrow}</div> : null}
      </div>
      <div className={`mt-3 font-mono-finance text-2xl font-semibold leading-tight ${toneClasses[tone]}`}>{value}</div>
      {helper ? <div className="mt-2 text-xs leading-5 text-lab-muted">{helper}</div> : null}
    </div>
  );
}
