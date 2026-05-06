"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import type { SeriesPoint } from "../lib/types";
import { formatCurrency, formatDate } from "./formatters";

type EquityChartProps = {
  equity: SeriesPoint[];
  benchmark: SeriesPoint[];
};

type TooltipPayload = {
  dataKey?: string;
  value?: number;
  color?: string;
  name?: string;
};

function EquityTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipPayload[]; label?: string }) {
  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div className="rounded-lg border border-lab-border bg-lab-bg/95 px-3 py-2 shadow-2xl">
      <div className="font-mono-finance text-xs text-lab-secondary">{label ? formatDate(label) : ""}</div>
      <div className="mt-2 space-y-1">
        {payload.map((item) => (
          <div key={item.dataKey} className="flex items-center justify-between gap-6 text-xs">
            <span className="text-lab-secondary" style={{ color: item.color }}>
              {item.name}
            </span>
            <span className="font-mono-finance text-lab-text">{formatCurrency(Number(item.value))}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function EquityChart({ equity, benchmark }: EquityChartProps) {
  const benchmarkByDate = new Map(benchmark.map((point) => [point.date, point.value]));
  const data = equity.map((point) => ({
    date: point.date,
    equity: point.value,
    benchmark: benchmarkByDate.get(point.date)
  }));

  return (
    <section className="rounded-xl border border-lab-border bg-lab-surface p-4 shadow-[0_24px_80px_rgba(0,0,0,0.22)]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-lab-text">Equity Curve</h2>
          <p className="mt-1 text-sm text-lab-secondary">Strategy equity compared with buy-and-hold when requested.</p>
        </div>
        <span className="rounded-full border border-lab-border bg-lab-card px-3 py-1 font-mono-finance text-xs text-lab-secondary">
          {equity.length} bars
        </span>
      </div>

      <div className="mt-4 h-[370px] rounded-xl border border-lab-border bg-lab-bg p-3">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 16, right: 18, left: 4, bottom: 4 }}>
            <CartesianGrid stroke="#1F2937" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: "#98A2B3", fontSize: 12, fontFamily: "monospace" }}
              tickLine={false}
              axisLine={{ stroke: "#253044" }}
              minTickGap={34}
            />
            <YAxis
              tick={{ fill: "#98A2B3", fontSize: 12, fontFamily: "monospace" }}
              tickLine={false}
              axisLine={{ stroke: "#253044" }}
              tickFormatter={formatCurrency}
              width={88}
            />
            <Tooltip content={<EquityTooltip />} cursor={{ stroke: "#3B82F6", strokeOpacity: 0.35 }} />
            <Legend wrapperStyle={{ color: "#98A2B3", fontSize: 12, paddingTop: 12 }} />
            <Line
              type="monotone"
              dataKey="equity"
              name="Strategy Equity"
              stroke="#38BDF8"
              strokeWidth={2.6}
              dot={false}
              activeDot={{ r: 4, stroke: "#E6EDF7", strokeWidth: 1 }}
            />
            {benchmark.length > 0 ? (
              <Line
                type="monotone"
                dataKey="benchmark"
                name="Benchmark"
                stroke="#667085"
                strokeWidth={2}
                dot={false}
                strokeDasharray="5 5"
              />
            ) : null}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
