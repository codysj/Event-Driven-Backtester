"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SeriesPoint } from "../lib/types";
import { formatPercent } from "./formatters";

type DrawdownChartProps = {
  drawdown: SeriesPoint[];
};

export function DrawdownChart({ drawdown }: DrawdownChartProps) {
  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/70 p-5">
      <h2 className="text-lg font-semibold text-slate-100">Drawdown</h2>
      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={drawdown}>
            <CartesianGrid stroke="#1e293b" />
            <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 12 }} minTickGap={28} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} tickFormatter={formatPercent} />
            <Tooltip formatter={(value) => formatPercent(Number(value))} contentStyle={{ background: "#020617", border: "1px solid #334155" }} />
            <Area type="monotone" dataKey="value" name="Drawdown" stroke="#fb7185" fill="#7f1d1d" fillOpacity={0.45} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

