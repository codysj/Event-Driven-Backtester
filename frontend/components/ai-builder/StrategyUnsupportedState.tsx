"use client";

import { AlertTriangle } from "lucide-react";

type StrategyUnsupportedStateProps = {
  unsupported: string[];
  validationErrors: string[];
};

export function StrategyUnsupportedState({ unsupported, validationErrors }: StrategyUnsupportedStateProps) {
  const items = [...unsupported, ...validationErrors];
  if (items.length === 0) {
    return null;
  }

  return (
    <section className="rounded-xl border border-lab-red/40 bg-lab-red/10 p-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 text-lab-red">
          <AlertTriangle size={17} />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-red-100">Needs Review</h3>
          <ul className="mt-2 space-y-1 text-sm leading-6 text-red-100/85">
            {items.map((item) => (
              <li key={item} className="break-words">
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
