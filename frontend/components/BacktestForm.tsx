"use client";

import { useMemo, useState } from "react";
import type { BacktestRequest, StrategyId, StrategyMetadata } from "../lib/types";

type BacktestFormProps = {
  strategies: StrategyMetadata[];
  isLoading: boolean;
  onSubmit: (request: BacktestRequest) => void;
};

const methodOptions = ["FIXED_DOLLAR", "FIXED_QUANTITY", "ALL_IN", "PERCENT_EQUITY", "VOLATILITY_TARGET"];

export function BacktestForm({ strategies, isLoading, onSubmit }: BacktestFormProps) {
  const [ticker, setTicker] = useState("AAPL");
  const [startDate, setStartDate] = useState("2020-01-01");
  const [endDate, setEndDate] = useState("2023-12-31");
  const [strategyId, setStrategyId] = useState<StrategyId>("momentum");
  const [initialCash, setInitialCash] = useState(100000);
  const [positionSizeMethod, setPositionSizeMethod] = useState("FIXED_DOLLAR");
  const [positionSizeValue, setPositionSizeValue] = useState(10000);
  const [commissionRate, setCommissionRate] = useState(0.001);
  const [slippageBps, setSlippageBps] = useState(5);
  const [benchmark, setBenchmark] = useState(true);
  const [parameters, setParameters] = useState<Record<string, number>>({
    fast_window: 10,
    slow_window: 50,
    window: 20,
    num_std: 2
  });

  const selectedStrategy = useMemo(
    () => strategies.find((strategy) => strategy.id === strategyId),
    [strategies, strategyId]
  );

  function submitForm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!ticker.trim()) return;

    const activeParameters: Record<string, number> = {};
    selectedStrategy?.parameters.forEach((parameter) => {
      activeParameters[parameter.name] = parameters[parameter.name] ?? parameter.default;
    });

    onSubmit({
      ticker,
      start_date: startDate,
      end_date: endDate,
      strategy: strategyId,
      initial_cash: initialCash,
      commission_rate: commissionRate,
      slippage_bps: slippageBps,
      position_size_method: positionSizeMethod,
      position_size_value: positionSizeValue,
      benchmark,
      parameters: activeParameters
    });
  }

  return (
    <form onSubmit={submitForm} className="space-y-5">
      <div>
        <label className="text-sm font-medium text-slate-300">Ticker</label>
        <input value={ticker} onChange={(event) => setTicker(event.target.value.toUpperCase())} className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-sky-400" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-sm font-medium text-slate-300">Start</label>
          <input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-sky-400" />
        </div>
        <div>
          <label className="text-sm font-medium text-slate-300">End</label>
          <input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-sky-400" />
        </div>
      </div>
      <div>
        <label className="text-sm font-medium text-slate-300">Strategy</label>
        <select value={strategyId} onChange={(event) => setStrategyId(event.target.value as StrategyId)} className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-sky-400">
          {strategies.map((strategy) => (
            <option key={strategy.id} value={strategy.id}>{strategy.name}</option>
          ))}
        </select>
        {selectedStrategy ? <p className="mt-2 text-xs leading-5 text-slate-500">{selectedStrategy.description}</p> : null}
      </div>
      <div className="grid grid-cols-2 gap-3">
        {selectedStrategy?.parameters.map((parameter) => (
          <div key={parameter.name}>
            <label className="text-sm font-medium text-slate-300">{parameter.label}</label>
            <input
              type="number"
              min={parameter.min}
              step={parameter.type === "integer" ? 1 : 0.1}
              value={parameters[parameter.name] ?? parameter.default}
              onChange={(event) => setParameters((current) => ({ ...current, [parameter.name]: Number(event.target.value) }))}
              className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-sky-400"
            />
          </div>
        ))}
      </div>
      <div>
        <label className="text-sm font-medium text-slate-300">Initial Cash</label>
        <input type="number" min={1} value={initialCash} onChange={(event) => setInitialCash(Number(event.target.value))} className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-sky-400" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-sm font-medium text-slate-300">Sizing</label>
          <select value={positionSizeMethod} onChange={(event) => setPositionSizeMethod(event.target.value)} className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-sky-400">
            {methodOptions.map((method) => <option key={method}>{method}</option>)}
          </select>
        </div>
        <div>
          <label className="text-sm font-medium text-slate-300">Size Value</label>
          <input type="number" min={0.0001} step={0.0001} value={positionSizeValue} onChange={(event) => setPositionSizeValue(Number(event.target.value))} className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-sky-400" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-sm font-medium text-slate-300">Commission</label>
          <input type="number" min={0} step={0.001} value={commissionRate} onChange={(event) => setCommissionRate(Number(event.target.value))} className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-sky-400" />
        </div>
        <div>
          <label className="text-sm font-medium text-slate-300">Slippage bps</label>
          <input type="number" min={0} value={slippageBps} onChange={(event) => setSlippageBps(Number(event.target.value))} className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100 outline-none focus:border-sky-400" />
        </div>
      </div>
      <label className="flex items-center gap-3 text-sm text-slate-300">
        <input type="checkbox" checked={benchmark} onChange={(event) => setBenchmark(event.target.checked)} className="h-4 w-4 rounded border-slate-700 bg-slate-950" />
        Include buy-and-hold benchmark
      </label>
      <button type="submit" disabled={isLoading} className="w-full rounded-md bg-sky-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-sky-300 disabled:cursor-not-allowed disabled:opacity-60">
        {isLoading ? "Running..." : "Run Backtest"}
      </button>
    </form>
  );
}

