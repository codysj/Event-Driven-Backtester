import type {
  BacktestRequest,
  BacktestResponse,
  GridSearchRequest,
  GridSearchResponse,
  HealthResponse,
  StrategyMetadata,
  WalkForwardRequest,
  WalkForwardResponse
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function fetchStrategies(): Promise<StrategyMetadata[]> {
  const response = await requestJson<{ strategies: StrategyMetadata[] }>("/api/strategies");
  return response.strategies;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/health");
}

export async function runBacktest(request: BacktestRequest): Promise<BacktestResponse> {
  return requestJson<BacktestResponse>("/api/backtest", {
    method: "POST",
    body: JSON.stringify(request)
  });
}

export async function runGridSearch(request: GridSearchRequest): Promise<GridSearchResponse> {
  return requestJson<GridSearchResponse>("/api/grid-search", {
    method: "POST",
    body: JSON.stringify(request)
  });
}

export async function runWalkForward(request: WalkForwardRequest): Promise<WalkForwardResponse> {
  return requestJson<WalkForwardResponse>("/api/walk-forward", {
    method: "POST",
    body: JSON.stringify(request)
  });
}
