import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import InvestigationForm from "../components/InvestigationForm.jsx";
import InvestigationResultView from "../components/InvestigationResultView.jsx";

export default function InvestigatePage() {
  const [defaultDate, setDefaultDate] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.dateRange().then((r) => setDefaultDate(r.max_date || "")).catch(() => {});
  }, []);

  const handleSubmit = async (payload) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.investigate(payload);
      setResult(data);
    } catch (e) {
      const detail = e?.response?.data?.detail;
      const message = typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => d.msg || JSON.stringify(d)).join("; ")
          : e.message || "Investigation failed";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">New Investigation</h2>
        <p className="text-xs text-ink3">
          Pick a metric and date. The Investigation Planner agent decides which dimensions to check and in what order — nothing here is a fixed scan.
        </p>
      </div>

      <InvestigationForm onSubmit={handleSubmit} loading={loading} defaultDate={defaultDate} />

      {error && (
        <div className="bg-bad/10 border border-bad/30 text-bad rounded-xl p-4 text-sm">{error}</div>
      )}

      {loading && (
        <div className="text-sm text-ink3 animate-pulse">
          Agents are investigating — metric monitoring → baseline → dimension exploration → root cause ranking…
        </div>
      )}

      <InvestigationResultView result={result} />
    </div>
  );
}
