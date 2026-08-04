import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ClipboardList } from "lucide-react";
import { api } from "../api/client.js";
import { SkeletonTable } from "../components/ui/Skeleton.jsx";
import EmptyState from "../components/ui/EmptyState.jsx";
import ErrorState from "../components/ui/ErrorState.jsx";

export default function InvestigationsList() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setError(null);
    api.listInvestigations().then(setItems).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Investigation History</h2>

      {error && <ErrorState message={`Couldn't load history: ${error}`} onRetry={load} />}

      {!error && items === null && <SkeletonTable rows={6} cols={4} />}

      {!error && items !== null && !items.length && (
        <EmptyState
          icon={ClipboardList}
          title="No investigations yet"
          message='Run one from "New Investigation" to see it here.'
        />
      )}

      {!error && items !== null && items.length > 0 && (
        <div className="bg-panel2 shadow-card rounded-xl overflow-hidden themed-transition">
          <table className="w-full text-sm">
            <thead className="bg-ink/5 text-ink3 text-left">
              <tr>
                <th className="px-4 py-2 font-normal">Date</th>
                <th className="px-4 py-2 font-normal">Metric</th>
                <th className="px-4 py-2 font-normal">Confidence</th>
                <th className="px-4 py-2 font-normal">Created</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.investigation_id} className="border-t border-line/60 hover:bg-ink/5 transition-colors duration-150">
                  <td className="px-4 py-2">
                    <Link to={`/history/${it.investigation_id}`} className="text-accent hover:underline">
                      {it.request?.target_date}
                    </Link>
                  </td>
                  <td className="px-4 py-2">{it.request?.metric}</td>
                  <td className="px-4 py-2">{((it.overall_confidence || 0) * 100).toFixed(0)}%</td>
                  <td className="px-4 py-2 text-ink3">{it.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
