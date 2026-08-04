export function Skeleton({ className = "", style }) {
  return <div className={`animate-pulse rounded-md bg-ink/10 ${className}`} style={style} />;
}

export function SkeletonKpiRow({ count = 5 }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-panel2 shadow-card rounded-xl p-4 flex flex-col gap-2">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-7 w-20" />
          <Skeleton className="h-3 w-24" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonChart({ height = 240, title = true }) {
  return (
    <div className="bg-panel2 shadow-card rounded-xl p-3">
      {title && (
        <div className="flex items-center justify-between mb-3 px-1">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-20" />
        </div>
      )}
      <Skeleton className="w-full" style={{ height }} />
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 5 }) {
  return (
    <div className="bg-panel2 shadow-card rounded-xl overflow-hidden">
      <div className="bg-ink/5 px-4 py-2 flex gap-6">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-3 w-16" />
        ))}
      </div>
      <div className="divide-y divide-line/60">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="px-4 py-3 flex gap-6">
            {Array.from({ length: cols }).map((_, c) => (
              <Skeleton key={c} className="h-3 w-16" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
