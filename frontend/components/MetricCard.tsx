type MetricCardProps = {
  label: string;
  value: string;
  helper?: string;
  tone?: "positive" | "negative" | "neutral";
};

const toneClasses = {
  positive: "text-emerald-300",
  negative: "text-rose-300",
  neutral: "text-slate-100"
};

export function MetricCard({ label, value, helper, tone = "neutral" }: MetricCardProps) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/80 p-4 shadow-sm">
      <div className="text-sm text-slate-400">{label}</div>
      <div className={`mt-2 text-2xl font-semibold ${toneClasses[tone]}`}>{value}</div>
      {helper ? <div className="mt-1 text-xs text-slate-500">{helper}</div> : null}
    </div>
  );
}

