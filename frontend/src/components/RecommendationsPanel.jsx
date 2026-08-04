export default function RecommendationsPanel({ recommendations = [] }) {
  return (
    <div className="bg-panel2 shadow-card rounded-xl themed-transition p-4">
      <h3 className="text-sm font-semibold text-ink2 mb-3">Recommendations</h3>
      <ul className="space-y-2">
        {recommendations.map((r, i) => (
          <li key={i} className="text-sm text-ink2 flex gap-2">
            <span className="text-accent shrink-0">→</span>
            <span>{r}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
