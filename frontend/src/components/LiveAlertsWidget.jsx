import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { api } from "../api/client.js";

const SEVERITY_STYLE = {
  high: "bg-bad/20 text-bad",
  medium: "bg-warn/20 text-warn",
  low: "bg-warn/20 text-warn",
  none: "bg-good/20 text-good",
};

export default function LiveAlertsWidget() {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const load = () => api.listAlerts({ limit: 5 }).then(setAlerts).catch(() => {});
    load();
    const t = setInterval(load, 20_000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="bg-panel2 shadow-card rounded-xl themed-transition p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-ink2">Live Alerts</h3>
        <Link to="/alerts" className="text-xs text-accent hover:underline">View all →</Link>
      </div>
      {!alerts.length && <div className="text-xs text-ink3">No alerts yet.</div>}
      <ul className="space-y-2">
        {alerts.map((a) => (
          <li key={a.id} className="flex items-center justify-between text-xs gap-2">
            <span className="text-ink2 capitalize truncate">{a.metric.replace("_", " ")} · {a.target_date}</span>
            <div className="flex items-center gap-2 shrink-0">
              <span className={`px-2 py-0.5 rounded-full ${SEVERITY_STYLE[a.severity] || SEVERITY_STYLE.none}`}>
                {a.severity}
              </span>
              <button
                type="button"
                title="Investigate with AI"
                onClick={() => navigate("/chat", { state: { mode: "anomaly-investigation", anomaly: a } })}
                className="text-accent hover:text-accent/80 transition-colors duration-150"
              >
                <Sparkles size={13} />
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
