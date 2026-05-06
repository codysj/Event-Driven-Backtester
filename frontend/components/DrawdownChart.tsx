"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SeriesPoint } from "../lib/types";
import { formatDate, formatPercent } from "./formatters";

type DrawdownChartProps = {
  drawdown: SeriesPoint[];
};

type TooltipPayload = {
  value?: number;
};

function DrawdownTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipPayload[]; label?: string }) {
  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div className="rounded-lg border border-lab-border bg-lab-bg/95 px-3 py-2 shadow-2xl">
      <div className="font-mono-finance text-xs text-lab-secondary">{label ? formatDate(label) : ""}</div>
      <div className="mt-1 font-mono-finance text-sm text-lab-red">{formatPercent(Number(payload[0].value))}</div>
    </div>
  );
}

export function DrawdownChart({ drawdown }: DrawdownChartProps) {
  return (
    <section className="rounded-xl border border-lab-border bg-lab-surface p-4 shadow-[0_24px_80px_rgba(0,0,0,0.2)]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-lab-text">Drawdown</h2>
          <p className="mt-1 text-sm text-lab-secondary">Peak-to-trough decline in portfolio equity.</p>
        </div>
      </div>
      <div className="mt-4 h-[260px] rounded-xl border border-lab-border bg-lab-bg p-3">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={drawdown} margin={{ top: 16, right: 18, left: 4, bottom: 4 }}>
            <defs>
              <linearGradient id="drawdownFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#EF4444" stopOpacity={0.24} />
                <stop offset="100%" stopColor="#EF4444" stopOpacity={0.04} />
              </linearGradient>
            </defs>
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
              tickFormatter={formatPercent}
              width={62}
            />
            <Tooltip content={<DrawdownTooltip />} cursor={{ stroke: "#EF4444", strokeOpacity: 0.35 }} />
            <Area
              type="monotone"
              dataKey="value"
              name="Drawdown"
              stroke="#EF4444"
              strokeWidth={2}
              fill="url(#drawdownFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
