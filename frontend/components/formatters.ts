export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2
  }).format(value);
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

export function formatDecimal(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "n/a";
  }
  return value.toFixed(2);
}

