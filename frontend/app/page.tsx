"use client";

import { useEffect, useMemo, useState } from "react";
import { AppShell } from "../components/AppShell";
import { BacktestForm } from "../components/BacktestForm";
import { GridSearchForm, WalkForwardForm } from "../components/ResearchForms";
import { GridSearchResults, WalkForwardResults } from "../components/ResearchResults";
import { ResultsDashboard } from "../components/ResultsDashboard";
import { fetchHealth, fetchStrategies, runBacktest, runGridSearch, runWalkForward } from "../lib/api";
import { DEFAULT_BACKTEST_REQUEST, DEFAULT_GRID_SEARCH_REQUEST, DEFAULT_WALK_FORWARD_REQUEST, FALLBACK_STRATEGIES } from "../lib/defaults";
import type {
  BacktestRequest,
  BacktestResponse,
  GridSearchRequest,
  GridSearchResponse,
  StrategyMetadata,
  WalkForwardRequest,
  WalkForwardResponse
} from "../lib/types";
import {
  hasErrors,
  validateBacktestRequest,
  validateGridSearchRequest,
  validateWalkForwardRequest,
  type FormErrors
} from "../lib/validation";

type ApiStatus = "checking" | "online" | "offline";
type LabMode = "backtest" | "grid" | "walk";

function cloneDefaultRequest(): BacktestRequest {
  return {
    ...DEFAULT_BACKTEST_REQUEST,
    parameters: { ...DEFAULT_BACKTEST_REQUEST.parameters }
  };
}

function cloneDefaultGridRequest(): GridSearchRequest {
  return {
    ...DEFAULT_GRID_SEARCH_REQUEST,
    parameter_grid: { ...DEFAULT_GRID_SEARCH_REQUEST.parameter_grid }
  };
}

function cloneDefaultWalkRequest(): WalkForwardRequest {
  return {
    ...DEFAULT_WALK_FORWARD_REQUEST,
    parameter_grid: { ...DEFAULT_WALK_FORWARD_REQUEST.parameter_grid }
  };
}

export default function HomePage() {
  const [strategies, setStrategies] = useState<StrategyMetadata[]>(FALLBACK_STRATEGIES);
  const [mode, setMode] = useState<LabMode>("backtest");
  const [request, setRequest] = useState<BacktestRequest>(cloneDefaultRequest);
  const [gridRequest, setGridRequest] = useState<GridSearchRequest>(cloneDefaultGridRequest);
  const [walkRequest, setWalkRequest] = useState<WalkForwardRequest>(cloneDefaultWalkRequest);
  const [result, setResult] = useState<BacktestResponse | null>(null);
  const [gridResult, setGridResult] = useState<GridSearchResponse | null>(null);
  const [walkResult, setWalkResult] = useState<WalkForwardResponse | null>(null);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [gridErrors, setGridErrors] = useState<FormErrors>({});
  const [walkErrors, setWalkErrors] = useState<FormErrors>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [gridError, setGridError] = useState<string | null>(null);
  const [walkError, setWalkError] = useState<string | null>(null);
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
    if (mode === "grid") {
      setGridRequest(cloneDefaultGridRequest());
      setGridErrors({});
      setGridError(null);
      return;
    }
    if (mode === "walk") {
      setWalkRequest(cloneDefaultWalkRequest());
      setWalkErrors({});
      setWalkError(null);
      return;
    }
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

  async function submitGridSearch(nextRequest = gridRequest) {
    const validationErrors = validateGridSearchRequest(nextRequest);
    setGridErrors(validationErrors);
    if (hasErrors(validationErrors)) {
      return;
    }

    setIsLoading(true);
    setGridError(null);
    try {
      const response = await runGridSearch({
        ...nextRequest,
        ticker: nextRequest.ticker.trim().toUpperCase()
      });
      setGridResult(response);
      setApiStatus("online");
    } catch (caught) {
      setGridError(caught instanceof Error ? caught.message : "Could not run the grid search.");
      setApiStatus("offline");
    } finally {
      setIsLoading(false);
    }
  }

  async function submitWalkForward(nextRequest = walkRequest) {
    const validationErrors = validateWalkForwardRequest(nextRequest);
    setWalkErrors(validationErrors);
    if (hasErrors(validationErrors)) {
      return;
    }

    setIsLoading(true);
    setWalkError(null);
    try {
      const response = await runWalkForward({
        ...nextRequest,
        ticker: nextRequest.ticker.trim().toUpperCase()
      });
      setWalkResult(response);
      setApiStatus("online");
    } catch (caught) {
      setWalkError(caught instanceof Error ? caught.message : "Could not run walk-forward validation.");
      setApiStatus("offline");
    } finally {
      setIsLoading(false);
    }
  }

  function runSelectedConfig(selectedRequest: BacktestRequest) {
    setMode("backtest");
    setRequest(selectedRequest);
    void submitBacktest(selectedRequest);
  }

  function runDefault() {
    const defaultRequest = cloneDefaultRequest();
    setRequest(defaultRequest);
    void submitBacktest(defaultRequest);
  }

  const configPanel =
    mode === "grid" ? (
      <GridSearchForm
        request={gridRequest}
        strategies={strategies}
        errors={gridErrors}
        isLoading={isLoading}
        onChange={setGridRequest}
        onSubmit={() => void submitGridSearch()}
        onReset={resetDefaults}
      />
    ) : mode === "walk" ? (
      <WalkForwardForm
        request={walkRequest}
        strategies={strategies}
        errors={walkErrors}
        isLoading={isLoading}
        onChange={setWalkRequest}
        onSubmit={() => void submitWalkForward()}
        onReset={resetDefaults}
      />
    ) : (
      <BacktestForm
        request={request}
        strategies={strategies}
        errors={formErrors}
        isLoading={isLoading}
        onChange={updateRequest}
        onSubmit={() => void submitBacktest()}
        onReset={resetDefaults}
      />
    );

  const activeRequest = mode === "grid" ? ({ ...request, ...gridRequest, parameters: request.parameters } as BacktestRequest) : mode === "walk" ? ({ ...request, ...walkRequest, parameters: request.parameters } as BacktestRequest) : request;
  const actionLabel = mode === "grid" ? "Run Grid Search" : mode === "walk" ? "Run Walk Forward" : "Run Backtest";
  const runActive = mode === "grid" ? () => void submitGridSearch() : mode === "walk" ? () => void submitWalkForward() : () => void submitBacktest();

  return (
    <AppShell
      request={activeRequest}
      strategies={strategies}
      apiStatus={apiStatus}
      isLoading={isLoading}
      onRun={runActive}
      onReset={resetDefaults}
      actionLabel={actionLabel}
      configPanel={configPanel}
    >
      <div className="mb-5 flex flex-wrap gap-2 rounded-xl border border-lab-border bg-lab-surface p-2">
        {[
          { id: "backtest", label: "Single Run" },
          { id: "grid", label: "Grid Search" },
          { id: "walk", label: "Walk-Forward" }
        ].map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setMode(item.id as LabMode)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              mode === item.id ? "bg-lab-blue text-white" : "text-lab-secondary hover:bg-lab-card hover:text-lab-text"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {mode === "grid" ? (
        <GridSearchResults result={gridResult} isLoading={isLoading} error={gridError} onRunSelected={runSelectedConfig} />
      ) : mode === "walk" ? (
        <WalkForwardResults result={walkResult} isLoading={isLoading} error={walkError} />
      ) : (
        <ResultsDashboard
          result={result}
          request={request}
          strategies={strategies}
          isLoading={isLoading}
          error={error}
          onRunDefault={runDefault}
        />
      )}

      <section id="docs" className="mt-5 rounded-xl border border-lab-border bg-lab-surface p-4">
        <h2 className="text-sm font-semibold text-lab-text">Local API</h2>
        <p className="mt-2 text-sm leading-6 text-lab-secondary">
          Start FastAPI with <code className="font-mono-finance text-lab-text">python -m uvicorn backtester.api.main:app --reload</code>. The dashboard calls the existing API and keeps backtesting logic server-side.
        </p>
      </section>
    </AppShell>
  );
}
