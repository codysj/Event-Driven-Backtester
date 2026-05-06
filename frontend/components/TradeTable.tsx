import type { Trade } from "../lib/types";
import { formatCurrency, formatDate, formatNumber } from "./formatters";

type TradeTableProps = {
  trades: Trade[];
};

export function TradeTable({ trades }: TradeTableProps) {
  return (
    <div id="trades" className="overflow-hidden rounded-xl border border-lab-border bg-lab-surface">
      <div className="flex items-center justify-between border-b border-lab-border px-4 py-3">
        <h3 className="text-sm font-semibold text-lab-text">Executions</h3>
        <span className="font-mono-finance text-xs text-lab-secondary">{trades.length} trades</span>
      </div>
      <div className="max-h-[420px] overflow-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="sticky top-0 z-10 border-b border-lab-border bg-lab-card text-xs uppercase tracking-[0.16em] text-lab-muted">
            <tr>
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium">Ticker</th>
              <th className="px-4 py-3 font-medium">Side</th>
              <th className="px-4 py-3 text-right font-medium">Qty</th>
              <th className="px-4 py-3 text-right font-medium">Price</th>
              <th className="px-4 py-3 text-right font-medium">Commission</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-lab-border/70">
            {trades.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-lab-secondary">
                  No trades were generated for this run.
                </td>
              </tr>
            ) : (
              trades.map((trade, index) => (
                <tr key={`${trade.timestamp}-${trade.side}-${index}`} className="bg-lab-surface transition hover:bg-lab-card/70">
                  <td className="whitespace-nowrap px-4 py-3 font-mono-finance text-lab-secondary">{formatDate(trade.timestamp)}</td>
                  <td className="px-4 py-3 font-mono-finance text-lab-text">{trade.ticker}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                        trade.side === "BUY"
                          ? "bg-emerald-500/10 text-lab-green"
                          : "bg-red-500/10 text-lab-red"
                      }`}
                    >
                      {trade.side}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono-finance text-lab-secondary">{formatNumber(trade.quantity)}</td>
                  <td className="px-4 py-3 text-right font-mono-finance text-lab-secondary">{formatCurrency(trade.price)}</td>
                  <td className="px-4 py-3 text-right font-mono-finance text-lab-secondary">{formatCurrency(trade.commission)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
