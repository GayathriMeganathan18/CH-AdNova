import ChartCard from "./charts/ChartCard.jsx";
import { useChartTheme, labelFor } from "./charts/theme.js";
import { fmt2 } from "./charts/chartUtils.js";

function fmtValue(metric, value) {
  if (metric === "ctr") return (value * 100).toFixed(2) + "%";
  if (metric === "fill_rate") return (value * 100).toFixed(1) + "%";
  return fmt2(value);
}

export default function DependencyTree({ tree, onRefresh }) {
  const { colors, NAMED_COLOR, tooltipTheme, baseChartOption } = useChartTheme();
  if (!tree) return null;
  const { root, children } = tree;

  function nodeFor(n) {
    const pct = n.deviation_pct >= 0 ? "+" : "";
    const color = NAMED_COLOR[n.color] || NAMED_COLOR.green;
    return {
      name: `${labelFor(n.metric)}\n${fmtValue(n.metric, n.actual)}  (${pct}${n.deviation_pct.toFixed(2)}%)`,
      itemStyle: { color, borderColor: color },
    };
  }

  const data = [{ ...nodeFor(root), children: children.map(nodeFor) }];

  const option = {
    ...baseChartOption,
    tooltip: {
      trigger: "item",
      triggerOn: "mousemove",
      ...tooltipTheme,
    },
    series: [
      {
        type: "tree",
        data,
        top: "8%",
        left: "14%",
        bottom: "8%",
        right: "26%",
        symbolSize: 14,
        orient: "LR",
        label: {
          position: "left",
          verticalAlign: "middle",
          align: "right",
          fontSize: 11,
          color: colors.textPrimary,
          lineHeight: 16,
        },
        leaves: {
          label: { position: "right", verticalAlign: "middle", align: "left" },
        },
        lineStyle: { color: colors.border },
        emphasis: { focus: "descendant" },
        expandAndCollapse: false,
        animationDuration: 400,
      },
    ],
  };

  const csvData = {
    headers: ["Metric", "Expected", "Actual", "Deviation %", "Severity"],
    rows: [root, ...children].map((n) => [n.metric, n.expected, n.actual, n.deviation_pct, n.severity]),
  };

  return <ChartCard title="Metric Dependency Tree" option={option} height={320} onRefresh={onRefresh} csvData={csvData} />;
}
