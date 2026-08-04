export default function RuledOutList({ items = [] }) {
  if (!items.length) return null;
  return (
    <div className="bg-panel2 shadow-card rounded-xl themed-transition p-4">
      <h3 className="text-sm font-semibold text-ink2 mb-3">Ruled Out</h3>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="text-sm text-ink3 flex gap-2">
            <span className="text-good shrink-0">✓</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
