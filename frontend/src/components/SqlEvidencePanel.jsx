export default function SqlEvidencePanel({ title, sql }) {
  if (!sql) return null;
  const statements = Array.isArray(sql) ? sql : [sql];

  return (
    <details className="bg-panel2 shadow-card rounded-xl themed-transition p-4 group">
      <summary className="text-sm font-semibold text-ink2 cursor-pointer select-none flex items-center gap-2">
        <span className="text-accent group-open:rotate-90 transition-transform inline-block">▶</span>
        {title || "SQL Evidence"}
      </summary>
      <div className="mt-3 space-y-3">
        {statements.map((s, i) => (
          <pre
            key={i}
            className="text-xs bg-surface border border-line/60 rounded-lg p-3 overflow-x-auto text-emerald-300 font-mono"
          >
            {s}
          </pre>
        ))}
      </div>
    </details>
  );
}
