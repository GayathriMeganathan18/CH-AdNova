import { AlertCircle, TrendingDown, TrendingUp } from "lucide-react";

const SEVERITY_STYLE = {
  high: "bg-bad/20 text-bad",
  medium: "bg-warn/20 text-warn",
  low: "bg-warn/20 text-warn",
  none: "bg-good/20 text-good",
};

export default function AnomalyContextCard({ anomaly }) {
  if (!anomaly) return null;
  const pct = anomaly.baseline?.deviation_pct ?? anomaly.score;
  const hasPct = typeof pct === "number";
  const isDown = hasPct && pct < 0;
  const TrendIcon = isDown ? TrendingDown : TrendingUp;

  return (
    <div className="bg-panel2 shadow-card rounded-xl p-4 themed-transition">
      <div className="flex items-center gap-2 mb-2">
        <AlertCircle size={14} className="text-accent" />
        <span className="text-xs font-semibold uppercase tracking-wide text-ink3">Investigating Anomaly</span>
      </div>

      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <div className="text-sm font-semibold text-ink capitalize">{anomaly.metric.replace("_", " ")}</div>
          {hasPct && (
            <div className={`flex items-center gap-1 text-sm font-medium ${isDown ? "text-bad" : "text-good"}`}>
              <TrendIcon size={14} />
              {Math.abs(pct).toFixed(1)}%
            </div>
          )}
        </div>
        {anomaly.severity && (
          <span className={`text-xs px-2 py-0.5 rounded-full capitalize shrink-0 ${SEVERITY_STYLE[anomaly.severity] || SEVERITY_STYLE.none}`}>
            {anomaly.severity} severity
          </span>
        )}
      </div>

      <div className="mt-2 pt-2 border-t border-line/60 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink3">
        <span>Date: {anomaly.target_date}</span>
        {anomaly.baseline && (
          <span>
            Baseline {anomaly.baseline.expected.toFixed(2)} → Actual {anomaly.baseline.actual.toFixed(2)}
          </span>
        )}
        {anomaly.source && <span className="capitalize">Source: {anomaly.source}</span>}
      </div>
    </div>
  );
}
