function SkeletonBlock({ className }: { className: string }) {
  return <div className={`animate-pulse rounded-xl bg-lab-card/80 ${className}`} />;
}

export function LoadingSkeleton() {
  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-lab-border bg-lab-surface p-5">
        <SkeletonBlock className="h-5 w-64" />
        <SkeletonBlock className="mt-3 h-4 w-96 max-w-full" />
      </div>
      <div className="grid gap-3 md:grid-cols-2 2xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, index) => (
          <SkeletonBlock key={index} className="h-28" />
        ))}
      </div>
      <SkeletonBlock className="h-[430px]" />
      <SkeletonBlock className="h-[310px]" />
    </div>
  );
}
