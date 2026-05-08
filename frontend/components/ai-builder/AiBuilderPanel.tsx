"use client";

import { Bot, Braces, Send } from "lucide-react";
import { useMemo, useState } from "react";
import { compileStrategyDraft, draftStrategyFromPrompt } from "../../lib/api";
import type { AiTargetMode, StrategyCompileResponse, StrategyDraftResponse } from "../../lib/types";
import { PromptTemplates } from "./PromptTemplates";
import { StrategyDraftPreview } from "./StrategyDraftPreview";

type AiBuilderPanelProps = {
  onLoadCompiled: (response: StrategyCompileResponse) => void;
};

function appendPrompt(current: string, template: string): string {
  const trimmed = current.trim();
  if (!trimmed) return template;
  return `${trimmed}\n${template}`;
}

function modeName(mode: AiTargetMode): string {
  if (mode === "single_run") return "Single Run";
  if (mode === "grid_search") return "Grid Search";
  if (mode === "walk_forward") return "Walk-Forward";
  return "the selected workflow";
}

function JsonBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <div className="rounded-lg border border-lab-border bg-lab-bg p-3">
      <div className="text-xs font-semibold uppercase tracking-[0.16em] text-lab-muted">{title}</div>
      <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap break-words font-mono-finance text-xs leading-5 text-lab-secondary">
        {JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}

export function AiBuilderPanel({ onLoadCompiled }: AiBuilderPanelProps) {
  const [prompt, setPrompt] = useState("");
  const [promptError, setPromptError] = useState<string | null>(null);
  const [draftResponse, setDraftResponse] = useState<StrategyDraftResponse | null>(null);
  const [compileResponse, setCompileResponse] = useState<StrategyCompileResponse | null>(null);
  const [isDrafting, setIsDrafting] = useState(false);
  const [isCompiling, setIsCompiling] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [compileError, setCompileError] = useState<string | null>(null);
  const [loadMessage, setLoadMessage] = useState<string | null>(null);

  const draft = draftResponse?.draft ?? null;
  const canShowJson = useMemo(() => draftResponse !== null || compileResponse !== null, [draftResponse, compileResponse]);
  const noDraftMessages = useMemo(
    () =>
      draftResponse && !draftResponse.draft
        ? Array.from(
            new Set([
              ...draftResponse.warnings,
              ...draftResponse.validation_errors,
              ...draftResponse.unsupported
            ])
          )
        : [],
    [draftResponse]
  );

  async function submitPrompt(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalized = prompt.trim();
    setPromptError(null);
    setApiError(null);
    setCompileError(null);
    setLoadMessage(null);
    setCompileResponse(null);

    if (!normalized) {
      setPromptError("Describe the strategy before generating a draft.");
      return;
    }

    setIsDrafting(true);
    try {
      const response = await draftStrategyFromPrompt({ prompt: normalized });
      setDraftResponse(response);
    } catch (caught) {
      setApiError(caught instanceof Error ? caught.message : "Could not create a strategy draft.");
      setDraftResponse(null);
    } finally {
      setIsDrafting(false);
    }
  }

  async function compileAndLoad() {
    if (!draft) return;

    setIsCompiling(true);
    setCompileError(null);
    setLoadMessage(null);
    try {
      const response = await compileStrategyDraft({ draft });
      setCompileResponse(response);
      if (response.status !== "ready" || !response.payload) {
        const details = [...response.validation_errors, ...response.unsupported].join(" ");
        setCompileError(details || "The draft could not be compiled yet.");
        return;
      }
      setLoadMessage(`Compiled request loaded into ${modeName(response.target_mode)}. Review the form before running.`);
      onLoadCompiled(response);
    } catch (caught) {
      setCompileError(caught instanceof Error ? caught.message : "Could not compile the strategy draft.");
    } finally {
      setIsCompiling(false);
    }
  }

  return (
    <div className="space-y-5">
      <section className="rounded-xl border border-lab-border bg-lab-surface p-5">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-lab-border bg-lab-card text-lab-cyan">
            <Bot size={18} />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-lab-text">AI Strategy Builder</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-lab-secondary">
              Turn a natural-language idea into a reviewed strategy draft, then compile it into an existing Backtest Lab request. The browser never sees API keys and never executes generated code.
            </p>
          </div>
        </div>

        <form onSubmit={submitPrompt} className="mt-5 space-y-4">
          <label className="block">
            <span className="text-sm font-medium text-lab-text">Prompt</span>
            <textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              rows={6}
              maxLength={2000}
              className="mt-2 w-full resize-y rounded-lg border border-lab-border bg-lab-bg px-3 py-3 text-sm leading-6 text-lab-text outline-none transition placeholder:text-lab-muted focus:border-lab-blue focus:ring-2 focus:ring-lab-blue/20"
              placeholder="Example: 20/100 SMA crossover on AAPL from 2020 to 2023 with benchmark analytics"
            />
            <div className="mt-1 flex items-center justify-between gap-3 text-xs">
              <span className="text-lab-red">{promptError}</span>
              <span className="font-mono-finance text-lab-muted">{prompt.length}/2000</span>
            </div>
          </label>

          <PromptTemplates onSelect={(template) => setPrompt((current) => appendPrompt(current, template))} />

          <button
            type="submit"
            disabled={isDrafting}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-lab-blue px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-950/30 transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Send size={16} />
            {isDrafting ? "Drafting..." : "Generate Draft"}
          </button>
        </form>

        {apiError ? <p className="mt-4 rounded-lg border border-lab-red/40 bg-lab-red/10 px-3 py-2 text-sm text-red-100">{apiError}</p> : null}
      </section>

      {isDrafting && !draftResponse ? (
        <section className="rounded-xl border border-lab-border bg-lab-surface p-6">
          <h2 className="text-base font-semibold text-lab-text">Drafting Strategy</h2>
          <p className="mt-2 text-sm leading-6 text-lab-secondary">Calling the FastAPI AI Builder endpoint and validating the returned draft.</p>
        </section>
      ) : null}

      {draft ? (
        <StrategyDraftPreview
          draft={draft}
          responseWarnings={draftResponse?.warnings ?? []}
          responseUnsupported={draftResponse?.unsupported ?? []}
          responseValidationErrors={draftResponse?.validation_errors ?? []}
          compileResponse={compileResponse}
          isCompiling={isCompiling}
          compileError={compileError}
          loadMessage={loadMessage}
          onCompileAndLoad={compileAndLoad}
        />
      ) : !isDrafting ? (
        <section className="rounded-xl border border-lab-border bg-lab-surface p-6">
          <h2 className="text-base font-semibold text-lab-text">
            {draftResponse ? "Draft Not Available" : "No Draft Yet"}
          </h2>
          {noDraftMessages.length > 0 ? (
            <ul className="mt-3 space-y-2 text-sm leading-6 text-amber-100">
              {noDraftMessages.map((message) => (
                <li key={message}>{message}</li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 max-w-3xl text-sm leading-6 text-lab-secondary">
              Generate a draft to inspect inferred dates, strategy parameters, costs, warnings, unsupported items, and compile-ready JSON.
            </p>
          )}
        </section>
      ) : null}

      {canShowJson ? (
        <details className="rounded-xl border border-lab-border bg-lab-surface p-5">
          <summary className="flex cursor-pointer items-center gap-2 text-sm font-semibold text-lab-text">
            <Braces size={16} />
            Reproducibility
          </summary>
          <div className="mt-4 grid gap-3 xl:grid-cols-3">
            <JsonBlock title="Original Prompt" value={prompt.trim()} />
            <JsonBlock title="Validated Draft JSON" value={draftResponse?.draft ?? null} />
            <JsonBlock title="Compiled Request JSON" value={compileResponse?.payload ?? null} />
          </div>
        </details>
      ) : null}
    </div>
  );
}
