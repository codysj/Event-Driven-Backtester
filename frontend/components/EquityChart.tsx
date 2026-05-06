"use client";

import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SeriesPoint } from "../lib/types";
import { formatCurrency } from "./formatters";

type EquityChartProps = {
  equity: SeriesPoint[];
  benchmark: SeriesPoint[];
};

export function EquityChart({ equity, benchmark }: EquityChartProps) {
  const benchmarkByDate = new Map(benchmark.map((point) => [point.date, point.value]));
  const data = equity.map((point) => ({
    date: point.date,
    equity: point.value,
    benchmark: benchmarkByDate.get(point.date)
  }));

  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/70 p-5">
      <h2 className="text-lg font-semibold text-slate-100">Equity Curve</h2>
      <div className="mt-4 h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="#1e293b" />
            <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 12 }} minTickGap={28} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} tickFormatter={formatCurrency} width={88} />
            <Tooltip formatter={(value) => formatCurrency(Number(value))} contentStyle={{ background: "#020617", border: "1px solid #334155" }} />
            <Legend />
            <Line type="monotone" dataKey="equity" name="Strategy" stroke="#38bdf8" strokeWidth={2} dot={false} />
            {benchmark.length > 0 ? <Line type="monotone" dataKey="benchmark" name="Benchmark" stroke="#94a3b8" strokeWidth={2} dot={false} /> : null}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

