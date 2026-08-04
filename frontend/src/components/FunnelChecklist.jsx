export default function FunnelChecklist({ checks = [] }) {
  return (
    <div className="bg-panel2 shadow-card rounded-xl themed-transition p-4">
      <h3 className="text-sm font-semibold text-ink2 mb-3">Funnel Check</h3>
      <ul className="space-y-2">
        {checks.map((c) => (
          <li key={c.stage} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2">
              <span className={c.is_abnormal ? "text-bad" : "text-good"}>
                {c.is_abnormal ? "✗" : "✓"}
              </span>
              <span className="capitalize text-ink">{c.stage.replace("_", " ")}</span>
            </span>
            <span className={c.is_abnormal ? "text-bad" : "text-ink3"}>
              {c.actual.toFixed(4)} ({c.pct_change >= 0 ? "+" : ""}{c.pct_change.toFixed(1)}%)
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
