import type { Trade } from "../lib/types";
import { formatCurrency } from "./formatters";

type TradeTableProps = {
  trades: Trade[];
};

export function TradeTable({ trades }: TradeTableProps) {
  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/70 p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">Trades</h2>
        <span className="text-sm text-slate-400">{trades.length} executions</span>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-slate-800 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="py-3 pr-4">Date</th>
              <th className="py-3 pr-4">Ticker</th>
              <th className="py-3 pr-4">Side</th>
              <th className="py-3 pr-4">Qty</th>
              <th className="py-3 pr-4">Price</th>
              <th className="py-3 pr-4">Commission</th>
            </tr>
          </thead>
          <tbody>
            {trades.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-6 text-center text-slate-500">
                  No trades were generated for this run.
                </td>
              </tr>
            ) : (
              trades.map((trade, index) => (
                <tr key={`${trade.timestamp}-${trade.side}-${index}`} className="border-b border-slate-800/70">
                  <td className="py-3 pr-4 text-slate-300">{trade.timestamp}</td>
                  <td className="py-3 pr-4 text-slate-300">{trade.ticker}</td>
                  <td className={`py-3 pr-4 font-medium ${trade.side === "BUY" ? "text-emerald-300" : "text-rose-300"}`}>{trade.side}</td>
                  <td className="py-3 pr-4 text-slate-300">{trade.quantity}</td>
                  <td className="py-3 pr-4 text-slate-300">{formatCurrency(trade.price)}</td>
                  <td className="py-3 pr-4 text-slate-300">{formatCurrency(trade.commission)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

