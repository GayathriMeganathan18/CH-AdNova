import ReactECharts from "echarts-for-react";
import { TrendingUp, TrendingDown } from "lucide-react";
import { useChartTheme } from "./charts/theme.js";

export default function KpiCard({ label, value, baseline, pctChange, format = (v) => v.toFixed(2), sparkline }) {
  const { colors } = useChartTheme();
  const isUp = pctChange >= 0;
  const isFlat = Math.abs(pctChange) < 8;
  const trendColor = isFlat ? "text-ink2" : isUp ? "text-good" : "text-bad";
  const sparkColor = isFlat ? colors.textMuted : isUp ? colors.good : colors.bad;
  const TrendIcon = isUp ? TrendingUp : TrendingDown;

  const sparkOption =
    sparkline && sparkline.length > 1
      ? {
          grid: { left: 0, right: 0, top: 4, bottom: 0 },
          xAxis: { type: "category", show: false, data: sparkline.map((_, i) => i) },
          yAxis: { type: "value", show: false, min: "dataMin", max: "dataMax" },
          series: [
            {
              type: "line",
              data: sparkline,
              showSymbol: false,
              smooth: true,
              lineStyle: { color: sparkColor, width: 1.5 },
              areaStyle: { color: sparkColor, opacity: 0.12 },
            },
          ],
          tooltip: { show: false },
        }
      : null;

  return (
    <div className="bg-panel2 shadow-card rounded-xl p-4 flex flex-col gap-1 themed-transition">
      <span className="text-xs uppercase tracking-wide text-ink3">{label}</span>
      <span className="text-2xl font-semibold text-ink">{format(value)}</span>
      <div className="flex items-center gap-2 text-xs">
        <span className={`flex items-center gap-0.5 font-medium ${trendColor}`}>
          <TrendIcon size={12} />
          {Math.abs(pctChange).toFixed(1)}%
        </span>
        <span className="text-ink3">vs baseline {format(baseline)}</span>
      </div>
      {sparkOption && (
        <div className="mt-1 -mx-1">
          <ReactECharts option={sparkOption} style={{ height: 32 }} notMerge lazyUpdate />
        </div>
      )}
    </div>
  );
}
