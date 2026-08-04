import ChartCard from "./charts/ChartCard.jsx";
import { useChartTheme } from "./charts/theme.js";

function withDeviation(daily) {
  return daily.map((d, i) => {
    const window = daily.slice(Math.max(0, i - 7), i);
    const avg = window.length ? window.reduce((s, w) => s + w.revenue, 0) / window.length : d.revenue;
    const pct = avg ? ((d.revenue - avg) / avg) * 100 : 0;
    return [d.day, Math.round(pct * 100) / 100];
  });
}

export default function CalendarHeatmap({ daily, onRefresh }) {
  const { colors, tooltipTheme, baseChartOption } = useChartTheme();
  if (!daily || daily.length < 2) return null;

  const data = withDeviation(daily);
  const range = Math.max(1, ...data.map((d) => Math.abs(d[1])));
  const minDate = daily[0].day;
  const maxDate = daily[daily.length - 1].day;

  const option = {
    ...baseChartOption,
    tooltip: {
      ...tooltipTheme,
      formatter: (p) => `${p.data[0]}<br/>revenue vs trailing avg: ${p.data[1] >= 0 ? "+" : ""}${p.data[1].toFixed(2)}%`,
    },
    visualMap: {
      min: -range,
      max: range,
      show: false,
      inRange: { color: [colors.bad, colors.panel2, colors.good] },
    },
    calendar: {
      top: 24,
      left: 30,
      right: 10,
      cellSize: ["auto", 16],
      range: [minDate, maxDate],
      itemStyle: { borderWidth: 2, borderColor: colors.panel },
      dayLabel: { color: colors.textMuted, fontSize: 10 },
      monthLabel: { color: colors.textMuted, fontSize: 10 },
      yearLabel: { show: false },
      splitLine: { lineStyle: { color: colors.border } },
    },
    series: [
      {
        type: "heatmap",
        coordinateSystem: "calendar",
        data,
      },
    ],
  };

  const csvData = { headers: ["Date", "Deviation %"], rows: data };

  return (
    <ChartCard
      title="Daily Revenue Deviation Calendar"
      option={option}
      height={200}
      onRefresh={onRefresh}
      csvData={csvData}
    />
  );
}
