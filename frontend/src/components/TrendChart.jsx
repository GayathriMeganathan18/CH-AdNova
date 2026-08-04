import ChartCard from "./charts/ChartCard.jsx";
import { useChartTheme } from "./charts/theme.js";
import { fmt2 } from "./charts/chartUtils.js";

export default function TrendChart({ title, days, values, color, valueFormatter, onRefresh }) {
  const { colors, tooltipTheme, axisLineTheme, axisLabelTheme, splitLineTheme, baseChartOption } = useChartTheme();
  const lineColor = color || colors.accent;

  const option = {
    ...baseChartOption,
    grid: { left: 48, right: 16, top: 12, bottom: 28 },
    tooltip: {
      trigger: "axis",
      ...tooltipTheme,
      valueFormatter: valueFormatter || ((v) => fmt2(v)),
    },
    xAxis: {
      type: "category",
      data: days,
      ...axisLineTheme,
      ...axisLabelTheme,
    },
    yAxis: {
      type: "value",
      ...splitLineTheme,
      ...axisLabelTheme,
    },
    series: [
      {
        data: values,
        type: "line",
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        itemStyle: { color: lineColor },
        lineStyle: { color: lineColor, width: 2 },
        areaStyle: { color: lineColor, opacity: 0.08 },
      },
    ],
  };

  const csvData = { headers: ["Date", title], rows: days.map((d, i) => [d, values[i]]) };

  return <ChartCard title={title} option={option} height={220} onRefresh={onRefresh} csvData={csvData} />;
}
