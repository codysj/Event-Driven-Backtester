import type { BacktestResponse, GridSearchResponse } from "./types";

function csvCell(value: unknown): string {
  const text = typeof value === "object" && value !== null ? JSON.stringify(value) : String(value ?? "");
  return `"${text.replaceAll('"', '""')}"`;
}

function downloadText(filename: string, mimeType: string, content: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function exportGridSearchCsv(result: GridSearchResponse): void {
  const header = [
    "rank",
    "parameters",
    "final_value",
    "total_return",
    "annualized_return",
    "sharpe_ratio",
    "sortino_ratio",
    "max_drawdown",
    "information_ratio",
    "profit_factor",
    "win_rate",
    "total_trades",
    "error"
  ];
  const rows = result.results.map((row) =>
    [
      row.rank,
      row.parameters,
      row.final_value,
      row.total_return,
      row.annualized_return,
      row.sharpe_ratio,
      row.sortino_ratio,
      row.max_drawdown,
      row.information_ratio,
      row.profit_factor,
      row.win_rate,
      row.total_trades,
      row.error
    ].map(csvCell).join(",")
  );
  downloadText("grid-search-results.csv", "text/csv;charset=utf-8", [header.join(","), ...rows].join("\n"));
}

export function exportBacktestTradesCsv(result: BacktestResponse): void {
  const header = ["timestamp", "ticker", "side", "quantity", "price", "commission"];
  const rows = result.trades.map((trade) =>
    [trade.timestamp, trade.ticker, trade.side, trade.quantity, trade.price, trade.commission].map(csvCell).join(",")
  );
  downloadText("backtest-trades.csv", "text/csv;charset=utf-8", [header.join(","), ...rows].join("\n"));
}

export function exportBacktestMetricsJson(result: BacktestResponse): void {
  downloadText("backtest-metrics.json", "application/json;charset=utf-8", JSON.stringify({ summary: result.summary, risk: result.risk }, null, 2));
}

export function exportConfigJson(config: Record<string, unknown>, filename = "backtest-config.json"): void {
  downloadText(filename, "application/json;charset=utf-8", JSON.stringify(config, null, 2));
}
