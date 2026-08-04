import { useState } from "react";
import { RotateCw } from "lucide-react";

const TIME_RANGES = [
  { value: "24h", label: "24H" },
  { value: "7d", label: "7D" },
  { value: "30d", label: "30D" },
  { value: "custom", label: "Custom" },
];

const REGIONS = ["APAC", "EU", "LATAM", "MEA", "NAM"];
const PUBLISHER_TIERS = ["tier_1", "tier_2", "tier_3"];

const selectClass =
  "bg-surface border border-line rounded-md pl-2 pr-1 py-1.5 text-xs text-ink focus:outline-none focus:ring-1 focus:ring-accent/50 transition-colors duration-150";
const labelClass = "flex flex-col gap-1 text-[11px] text-ink3 uppercase tracking-wide";

export default function FilterBar({ value, onChange, onRefresh, refreshing }) {
  const [localCustom, setLocalCustom] = useState({ start: value.customStart || "", end: value.customEnd || "" });

  const set = (patch) => onChange({ ...value, ...patch });

  return (
    <div className="bg-panel2 shadow-card rounded-xl p-3 flex flex-wrap items-end gap-3 themed-transition">
      <label className={labelClass}>
        Time Range
        <div className="flex bg-surface border border-line rounded-md p-0.5">
          {TIME_RANGES.map((r) => (
            <button
              key={r.value}
              type="button"
              onClick={() => set({ timeRange: r.value })}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors duration-150 ${
                value.timeRange === r.value ? "bg-accent/20 text-accent" : "text-ink3 hover:text-ink"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </label>

      {value.timeRange === "custom" && (
        <label className={labelClass}>
          Date Range
          <div className="flex items-center gap-1">
            <input
              type="date"
              value={localCustom.start}
              onChange={(e) => {
                const next = { ...localCustom, start: e.target.value };
                setLocalCustom(next);
                set({ customStart: next.start, customEnd: next.end });
              }}
              className={selectClass}
            />
            <span className="text-ink3 text-xs">→</span>
            <input
              type="date"
              value={localCustom.end}
              onChange={(e) => {
                const next = { ...localCustom, end: e.target.value };
                setLocalCustom(next);
                set({ customStart: next.start, customEnd: next.end });
              }}
              className={selectClass}
            />
          </div>
        </label>
      )}

      <label className={labelClass}>
        App
        <input
          type="text"
          placeholder="All apps"
          value={value.app}
          onChange={(e) => set({ app: e.target.value })}
          className={`${selectClass} w-32`}
        />
      </label>

      <label className={labelClass}>
        Region
        <select value={value.region} onChange={(e) => set({ region: e.target.value })} className={selectClass}>
          <option value="">All regions</option>
          {REGIONS.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </label>

      <label className={labelClass}>
        Publisher Tier
        <select value={value.publisherTier} onChange={(e) => set({ publisherTier: e.target.value })} className={selectClass}>
          <option value="">All tiers</option>
          {PUBLISHER_TIERS.map((t) => (
            <option key={t} value={t}>{t.replace("_", " ")}</option>
          ))}
        </select>
      </label>

      <button
        type="button"
        onClick={onRefresh}
        disabled={refreshing}
        className="ml-auto flex items-center gap-1.5 text-xs font-medium bg-accent/20 text-accent px-3 py-1.5 rounded-md hover:bg-accent/30 transition-colors duration-150 disabled:opacity-50"
      >
        <RotateCw size={12} className={refreshing ? "animate-spin" : ""} />
        Refresh
      </button>
    </div>
  );
}
