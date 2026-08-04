import { useEffect, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { BellOff, Sparkles } from "lucide-react";
import { api } from "../api/client.js";
import { SkeletonTable } from "../components/ui/Skeleton.jsx";
import EmptyState from "../components/ui/EmptyState.jsx";
import ErrorState from "../components/ui/ErrorState.jsx";

const SEVERITY_STYLE = {
  high: "bg-bad/20 text-bad",
  medium: "bg-warn/20 text-warn",
  low: "bg-warn/20 text-warn",
  none: "bg-good/20 text-good",
};

const METRICS = ["revenue", "requests", "fill_rate", "ctr", "ecpm", "impressions", "clicks"];
const SEVERITIES = ["low", "medium", "high"];
const STATUSES = ["detected", "investigated"];

function MonitorStatusBanner() {
  const [status, setStatus] = useState(null);
  const [running, setRunning] = useState(false);

  const load = useCallback(() => {
    api.monitorStatus().then(setStatus).catch(() => setStatus(null));
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 15_000);
    return () => clearInterval(t);
  }, [load]);

  const runNow = async () => {
    setRunning(true);
    try {
      await api.runMonitorNow();
      load();
    } finally {
      setRunning(false);
    }
  };

  if (!status) return null;

  return (
    <div className="bg-panel2 shadow-card rounded-xl p-4 flex items-center justify-between flex-wrap gap-3">
      <div className="flex items-center gap-3 text-sm">
        <span className={`w-2 h-2 rounded-full ${status.enabled ? "bg-good" : "bg-bad"}`} />
        <span className="text-ink">
          Real-time monitor {status.enabled ? "running" : "disabled"} · checks {status.monitored_metrics.length} metrics every {status.interval_seconds}s · strategy: {status.strategy}
        </span>
        {status.last_run_at && (
          <span className="text-ink3 text-xs">
            last run {new Date(status.last_run_at).toLocaleTimeString()}
          </span>
        )}
      </div>
      <button
        onClick={runNow}
        disabled={running}
        className="text-xs bg-accent/20 text-accent px-3 py-1.5 rounded-md hover:bg-accent/30 disabled:opacity-50"
      >
        {running ? "Checking…" : "Run check now"}
      </button>
    </div>
  );
}

export default function AlertHistory() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ metric: "", severity: "", status: "" });

  const load = useCallback(() => {
    setLoading(true);
    const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v));
    api
      .listAlerts(params)
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [filters]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Alert History</h2>
        <p className="text-xs text-ink3">
          Every anomaly the real-time monitor or a manual check has detected, with the root cause once investigated.
        </p>
      </div>

      <MonitorStatusBanner />

      <div className="bg-panel2 shadow-card rounded-xl p-4 flex flex-wrap gap-3 items-end">
        <label className="flex flex-col gap-1 text-xs text-ink3">
          Metric
          <select
            className="bg-surface border border-line rounded-md px-2 py-1.5 text-sm text-ink"
            value={filters.metric}
            onChange={(e) => setFilters((f) => ({ ...f, metric: e.target.value }))}
          >
            <option value="">All</option>
            {METRICS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-ink3">
          Severity
          <select
            className="bg-surface border border-line rounded-md px-2 py-1.5 text-sm text-ink"
            value={filters.severity}
            onChange={(e) => setFilters((f) => ({ ...f, severity: e.target.value }))}
          >
            <option value="">All</option>
            {SEVERITIES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs text-ink3">
          Status
          <select
            className="bg-surface border border-line rounded-md px-2 py-1.5 text-sm text-ink"
            value={filters.status}
            onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
          >
            <option value="">All</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>
        <button
          onClick={() => setFilters({ metric: "", severity: "", status: "" })}
          className="text-xs text-ink3 hover:text-ink px-2 py-1.5"
        >
          Clear filters
        </button>
      </div>

      {error && <ErrorState message={`Couldn't load alert history: ${error}`} onRetry={load} />}
      {loading && !error && <SkeletonTable rows={6} cols={6} />}

      {!loading && !error && !items.length && (
        <EmptyState icon={BellOff} title="No alerts recorded yet" message="The real-time monitor will populate this once it detects an anomaly." />
      )}

      {!loading && !error && items.length > 0 && (
        <div className="bg-panel2 shadow-card rounded-xl overflow-hidden themed-transition">
          <table className="w-full text-sm">
            <thead className="bg-ink/5 text-ink3 text-left">
              <tr>
                <th className="px-4 py-2 font-normal">Date</th>
                <th className="px-4 py-2 font-normal">Metric</th>
                <th className="px-4 py-2 font-normal">Severity</th>
                <th className="px-4 py-2 font-normal">Source</th>
                <th className="px-4 py-2 font-normal">Status</th>
                <th className="px-4 py-2 font-normal">Root Cause</th>
                <th className="px-4 py-2 font-normal">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id} className="border-t border-line/60 hover:bg-ink/5 transition-colors duration-150">
                  <td className="px-4 py-2 text-ink2">{it.target_date}</td>
                  <td className="px-4 py-2 capitalize">{it.metric.replace("_", " ")}</td>
                  <td className="px-4 py-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${SEVERITY_STYLE[it.severity] || SEVERITY_STYLE.none}`}>
                      {it.severity}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-ink3 text-xs">{it.source || "manual"}</td>
                  <td className="px-4 py-2 text-ink3 text-xs">{it.status || "detected"}</td>
                  <td className="px-4 py-2">
                    {it.investigation_id ? (
                      <Link to={`/history/${it.investigation_id}`} className="text-accent hover:underline">
                        {it.root_cause_summary || "View investigation"} ↗
                      </Link>
                    ) : (
                      <span className="text-ink3 text-xs">not investigated</span>
                    )}
                  </td>
                  <td className="px-4 py-2">
                    <button
                      type="button"
                      onClick={() => navigate("/chat", { state: { mode: "anomaly-investigation", anomaly: it } })}
                      className="inline-flex items-center gap-1.5 text-xs font-medium bg-accent/10 text-accent px-2.5 py-1.5 rounded-md hover:bg-accent/20 transition-colors duration-150"
                    >
                      <Sparkles size={12} />
                      Investigate with AI
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
