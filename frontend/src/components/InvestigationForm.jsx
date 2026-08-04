import { useState } from "react";

const METRICS = ["revenue", "requests", "fill_rate", "ctr", "ecpm"];

export default function InvestigationForm({ onSubmit, loading, defaultDate }) {
  const [metric, setMetric] = useState("revenue");
  const [targetDate, setTargetDate] = useState(defaultDate || "");
  const [baselineDays, setBaselineDays] = useState(7);

  const submit = (e) => {
    e.preventDefault();
    if (!targetDate) return;
    onSubmit({ metric, target_date: targetDate, baseline_days: Number(baselineDays) });
  };

  return (
    <form onSubmit={submit} className="bg-panel2 shadow-card rounded-xl themed-transition p-5 flex flex-wrap gap-4 items-end">
      <div className="flex flex-col gap-1">
        <label className="text-xs text-ink3">Metric</label>
        <select
          value={metric}
          onChange={(e) => setMetric(e.target.value)}
          className="bg-surface border border-line rounded-md px-3 py-2 text-sm"
        >
          {METRICS.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-ink3">Target Date</label>
        <input
          type="date"
          value={targetDate}
          onChange={(e) => setTargetDate(e.target.value)}
          required
          className="bg-surface border border-line rounded-md px-3 py-2 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-xs text-ink3">Baseline Days</label>
        <input
          type="number"
          min={1}
          max={30}
          value={baselineDays}
          onChange={(e) => setBaselineDays(e.target.value)}
          className="bg-surface border border-line rounded-md px-3 py-2 text-sm w-24"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="bg-accent text-black font-medium text-sm px-5 py-2 rounded-md hover:bg-accent/80 disabled:opacity-50"
      >
        {loading ? "Investigating…" : "Run Investigation"}
      </button>
    </form>
  );
}
