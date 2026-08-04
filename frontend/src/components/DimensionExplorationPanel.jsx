import SqlEvidencePanel from "./SqlEvidencePanel.jsx";

export default function DimensionExplorationPanel({ explorations = [] }) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-ink2">Dimension Exploration</h3>
      {explorations.map((exp, i) => (
        <div
          key={exp.dimension}
          className={`rounded-xl p-4 ${
            exp.is_significant ? "border border-warn/40 bg-warn/5" : "bg-panel2 shadow-card"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium capitalize">
              {i + 1}. {exp.dimension}
            </span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full ${
                exp.is_significant ? "bg-warn/20 text-warn" : "bg-ink/5 text-ink3"
              }`}
            >
              {exp.is_significant ? "FLAGGED" : "normal"}
            </span>
          </div>

          {exp.top_contributor && (
            <table className="w-full text-xs mb-2">
              <thead>
                <tr className="text-ink3 text-left">
                  <th className="font-normal pb-1">Value</th>
                  <th className="font-normal pb-1">Baseline</th>
                  <th className="font-normal pb-1">Actual</th>
                  <th className="font-normal pb-1">Share of Delta</th>
                </tr>
              </thead>
              <tbody>
                {exp.all_values.slice(0, 5).map((v) => (
                  <tr
                    key={v.value}
                    className={v.value === exp.top_contributor.value ? "text-ink" : "text-ink3"}
                  >
                    <td className="py-0.5">{v.value}</td>
                    <td className="py-0.5">{v.baseline_metric.toFixed(2)}</td>
                    <td className="py-0.5">{v.actual_metric.toFixed(2)}</td>
                    <td className="py-0.5">{v.share_of_total_delta_pct.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <SqlEvidencePanel title="SQL used for this dimension" sql={exp.sql} />
        </div>
      ))}
    </div>
  );
}
