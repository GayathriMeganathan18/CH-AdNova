import ChartCard from "./charts/ChartCard.jsx";
import { useChartTheme } from "./charts/theme.js";

export default function FunnelChart({ volumes, onRefresh }) {
  const { colors, tooltipTheme, baseChartOption } = useChartTheme();
  if (!volumes) return null;

  const STAGE_COLOR = [colors.accent, colors.good, colors.warn, colors.bad];
  const stages = [
    { name: "Requests", value: volumes.requests },
    { name: "Fills", value: volumes.fills },
    { name: "Impressions", value: volumes.impressions },
    { name: "Clicks", value: volumes.clicks },
  ];

  const option = {
    ...baseChartOption,
    tooltip: {
      trigger: "item",
      ...tooltipTheme,
      formatter: (p) => `${p.name}: ${p.value.toLocaleString()} (${p.percent.toFixed(2)}%)`,
    },
    series: [
      {
        type: "funnel",
        left: "8%",
        right: "8%",
        top: 16,
        bottom: 10,
        min: 0,
        max: stages[0].value || 1,
        sort: "none",
        gap: 3,
        label: { show: true, position: "inside", color: "#0b0e12", fontSize: 11, fontWeight: 600 },
        itemStyle: { borderColor: colors.panel, borderWidth: 1 },
        data: stages.map((s, i) => ({ ...s, itemStyle: { color: STAGE_COLOR[i] } })),
      },
    ],
  };

  const csvData = { headers: ["Stage", "Volume"], rows: stages.map((s) => [s.name, s.value]) };

  return <ChartCard title="Conversion Funnel" option={option} height={220} onRefresh={onRefresh} csvData={csvData} />;
}
