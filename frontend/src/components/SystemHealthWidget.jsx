import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import ViewClickStackButton from "./ViewClickStackButton.jsx";

const LABEL = {
  clickhouse: "ClickHouse",
  mongodb: "MongoDB",
  langfuse: "Langfuse",
  clickstack: "ClickStack",
  monitor: "Monitor",
};

export default function SystemHealthWidget() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const load = () => api.systemHealth().then(setHealth).catch(() => setHealth(null));
    load();
    const t = setInterval(load, 20_000);
    return () => clearInterval(t);
  }, []);

  if (!health) return null;

  return (
    <div className="bg-panel2 shadow-card rounded-xl themed-transition p-4">
      <div className="flex items-center justify-between mb-3 gap-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-ink2">System Health</h3>
          <span className={`text-xs px-2 py-0.5 rounded-full ${health.status === "ok" ? "bg-good/20 text-good" : "bg-bad/20 text-bad"}`}>
            {health.status}
          </span>
        </div>
        <ViewClickStackButton url={health.components?.clickstack?.url ?? null} />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {Object.entries(health.components).map(([key, c]) => (
          <div key={key} className="flex items-center gap-2 text-xs" title={c.note || ""}>
            <span className={`w-2 h-2 rounded-full ${c.up ? "bg-good" : c.required ? "bg-bad" : "bg-warn"}`} />
            <span className="text-ink2">{LABEL[key] || key}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
