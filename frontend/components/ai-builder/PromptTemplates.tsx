"use client";

const templates = [
  "20/100 SMA crossover on AAPL",
  "Mean reversion on MSFT",
  "Optimize SMA windows",
  "Walk-forward validate momentum",
  "Compare against SPY benchmark"
];

type PromptTemplatesProps = {
  onSelect: (template: string) => void;
};

export function PromptTemplates({ onSelect }: PromptTemplatesProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {templates.map((template) => (
        <button
          key={template}
          type="button"
          onClick={() => onSelect(template)}
          className="rounded-lg border border-lab-border bg-lab-card px-3 py-2 text-xs text-lab-secondary transition hover:border-lab-blue hover:text-lab-text"
        >
          {template}
        </button>
      ))}
    </div>
  );
}
