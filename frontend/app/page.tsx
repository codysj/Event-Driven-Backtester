"use client";

import { useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { BacktestForm } from "../components/BacktestForm";
import { ResultsDashboard } from "../components/ResultsDashboard";
import { fetchHealth, fetchStrategies, runBacktest } from "../lib/api";
import { DEFAULT_BACKTEST_REQUEST, FALLBACK_STRATEGIES } from "../lib/defaults";
import type { BacktestRequest, BacktestResponse, StrategyMetadata } from "../lib/types";
import { hasErrors, validateBacktestRequest, type FormErrors } from "../lib/validation";

type ApiStatus = "checking" | "online" | "offline";

function cloneDefaultRequest(): BacktestRequest {
  return {
    ...DEFAULT_BACKTEST_REQUEST,
    parameters: { ...DEFAULT_BACKTEST_REQUEST.parameters }
  };
}

export default function HomePage() {
  const [strategies, setStrategies] = useState<StrategyMetadata[]>(FALLBACK_STRATEGIES);
  const [request, setRequest] = useState<BacktestRequest>(cloneDefaultRequest);
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");

  useEffect(() => {
    fetchHealth()
      .then(() => setApiStatus("online"))
      .catch(() => setApiStatus("offline"));

    fetchStrategies()
      .then((items) => {
        setStrategies(items);
        setApiStatus("online");
      })
      .catch(() => setStrategies(FALLBACK_STRATEGIES));
  }, []);

  const selectedStrategy = useMemo(
    () => strategies.find((strategy) => strategy.id === request.strategy),
    [request.strategy, strategies]
  );

  function updateRequest(nextRequest: BacktestRequest) {
    setRequest(nextRequest);
    if (Object.keys(formErrors).length > 0) {
      const strategy = strategies.find((item) => item.id === nextRequest.strategy);
      setFormErrors(validateBacktestRequest(nextRequest, strategy));
    }
  }

  function resetDefaults() {
    setRequest(cloneDefaultRequest());
    setFormErrors({});
    setError(null);
  }

  async function submitBacktest(nextRequest = request) {
    const strategy = strategies.find((item) => item.id === nextRequest.strategy) ?? selectedStrategy;
    const validationErrors = validateBacktestRequest(nextRequest, strategy);
    setFormErrors(validationErrors);
    if (hasErrors(validationErrors)) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await runBacktest({
        ...nextRequest,
        ticker: nextRequest.ticker.trim().toUpperCase()
      });
      setResult(response);
      setApiStatus("online");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not run the backtest.");
      setApiStatus("offline");
    } finally {
      setIsLoading(false);
    }
  }

  function runDefault() {
    const defaultRequest = cloneDefaultRequest();
    setRequest(defaultRequest);
    void submitBacktest(defaultRequest);
  }

  return (
    <AppShell
      request={request}
      strategies={strategies}
      apiStatus={apiStatus}
      isLoading={isLoading}
      onRun={() => void submitBacktest()}
      onReset={resetDefaults}
      configPanel={
        <BacktestForm
          request={request}
          strategies={strategies}
          errors={formErrors}
          isLoading={isLoading}
          onChange={updateRequest}
          onSubmit={() => void submitBacktest()}
          onReset={resetDefaults}
        />
      }
    >
      <ResultsDashboard
        result={result}
        request={request}
        strategies={strategies}
        isLoading={isLoading}
        error={error}
        onRunDefault={runDefault}
      />

      <section id="docs" className="mt-5 rounded-xl border border-lab-border bg-lab-surface p-4">
        <h2 className="text-sm font-semibold text-lab-text">Local API</h2>
        <p className="mt-2 text-sm leading-6 text-lab-secondary">
          Start FastAPI with <code className="font-mono-finance text-lab-text">python -m uvicorn backtester.api.main:app --reload</code>. The dashboard calls the existing API and keeps backtesting logic server-side.
        </p>
      </section>
    </AppShell>
  );
}
