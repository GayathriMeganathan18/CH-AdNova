import SqlEvidencePanel from "./SqlEvidencePanel.jsx";

export default function CounterfactualCard({ counterfactual }) {
  if (!counterfactual) return null;
  const { scenario, projected_metric, actual_metric, recovered_value, sql } = counterfactual;

  return (
    <div className="bg-panel2 shadow-card rounded-xl themed-transition p-4 space-y-3">
      <h3 className="text-sm font-semibold text-ink2">Counterfactual Simulator</h3>
      <p className="text-sm text-ink3">"What if {scenario}?"</p>
      <div className="grid grid-cols-3 gap-3 text-center">
        <div>
          <div className="text-xs text-ink3">Actual</div>
          <div className="text-lg font-semibold">{actual_metric.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-xs text-ink3">Projected</div>
          <div className="text-lg font-semibold text-accent">{projected_metric.toFixed(2)}</div>
        </div>
        <div>
          <div className="text-xs text-ink3">Recoverable</div>
          <div className="text-lg font-semibold text-good">+{recovered_value.toFixed(2)}</div>
        </div>
      </div>
      <SqlEvidencePanel title="Simulation SQL" sql={sql} />
    </div>
  );
}
