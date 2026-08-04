import ChartCard from "./charts/ChartCard.jsx";
import { useChartTheme, labelFor } from "./charts/theme.js";

export default function DrilldownSunburst({ drilldowns, onRefresh }) {
  const { colors, tooltipTheme, baseChartOption } = useChartTheme();
  if (!drilldowns || !drilldowns.length) return null;

  const byParent = {};
  drilldowns.forEach((f) => {
    const key = `${f.parent_dimension}:${f.parent_value}`;
    (byParent[key] = byParent[key] || []).push(f);
  });

  function childrenFor(dimension, value) {
    const key = `${dimension}:${value}`;
    return (byParent[key] || []).map((f) => ({
      name: labelFor(f.dimension),
      value: Math.max(1, Math.abs(f.top_contributor?.delta || 0)),
      itemStyle: { color: f.is_significant ? colors.bad : colors.border },
      children: f.top_contributor
        ? [
            {
              name: f.top_contributor.value,
              value: Math.max(1, Math.abs(f.top_contributor.delta)),
              itemStyle: { color: f.is_significant ? colors.warn : colors.gridLine },
              children: childrenFor(f.dimension, f.top_contributor.value),
            },
          ]
        : [],
    }));
  }

  const roots = [
    ...new Set(drilldowns.filter((f) => f.depth === 1).map((f) => `${f.parent_dimension}:${f.parent_value}`)),
  ];
  const data = roots.map((key) => {
    const [dim, value] = key.split(":");
    return {
      name: `${labelFor(dim)}: ${value}`,
      itemStyle: { color: colors.accent },
      children: childrenFor(dim, value),
    };
  });

  if (!data.length) return null;

  const option = {
    ...baseChartOption,
    tooltip: { ...tooltipTheme, formatter: (p) => p.name },
    series: [
      {
        type: "sunburst",
        radius: [0, "90%"],
        data,
        label: { color: colors.textPrimary, fontSize: 10 },
        itemStyle: { borderColor: colors.panel, borderWidth: 1 },
        emphasis: { focus: "ancestor" },
      },
    ],
  };

  const csvData = {
    headers: ["Depth", "Parent", "Dimension", "Significant", "Top Value", "Share %"],
    rows: drilldowns.map((d) => [
      d.depth,
      `${d.parent_dimension}=${d.parent_value}`,
      d.dimension,
      d.is_significant ? "yes" : "no",
      d.top_contributor?.value ?? "",
      d.top_contributor?.share_of_parent_delta_pct ?? "",
    ]),
  };

  return (
    <ChartCard title="Recursive Drilldown" option={option} height={320} onRefresh={onRefresh} csvData={csvData} />
  );
}
