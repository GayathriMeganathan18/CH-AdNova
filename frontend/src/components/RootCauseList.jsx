import ConfidenceGauge from "./ConfidenceGauge.jsx";

export default function RootCauseList({ rootCauses = [] }) {
  if (!rootCauses.length) {
    return (
      <div className="bg-panel2 shadow-card rounded-xl themed-transition p-4 text-sm text-ink3">
        No concentrated root cause found — the anomaly appears broad-based rather than isolated to one segment.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-ink2">Root Cause Ranking</h3>
      {rootCauses.map((rc) => (
        <div key={rc.rank} className="bg-panel2 shadow-card rounded-xl themed-transition p-4 flex items-center gap-4">
          <ConfidenceGauge confidence={rc.confidence} size={100} />
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs bg-accent/20 text-accent px-2 py-0.5 rounded-full">#{rc.rank}</span>
              <span className="font-medium">
                {rc.hypothesis.dimension} = "{rc.hypothesis.value}"
              </span>
            </div>
            <p className="text-sm text-ink3 mb-1">{rc.hypothesis.statement}</p>
            <p className="text-xs text-ink3">{rc.hypothesis.validation_note}</p>
            <div className="flex gap-4 mt-2 text-xs">
              <span className="text-ink3">
                Impact: <span className="text-ink">{rc.business_impact_value.toFixed(2)}</span>
              </span>
              <span className="text-ink3">
                Share: <span className="text-ink">{rc.business_impact_pct.toFixed(1)}%</span>
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
