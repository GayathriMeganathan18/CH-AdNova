import ChartCard from "./charts/ChartCard.jsx";
import { useChartTheme } from "./charts/theme.js";
import { fmt2 } from "./charts/chartUtils.js";

export default function TimeSeriesForecastChart({ title, data, onRefresh }) {
  const { colors, tooltipTheme, axisLineTheme, axisLabelTheme, splitLineTheme, baseChartOption } = useChartTheme();
  if (!data) return null;
  const { labels, values, forecast_labels: forecastLabels, forecast_values: forecastValues } = data;
  const n = labels.length;
  const f = forecastValues.length;

  const allLabels = [...labels, ...forecastLabels];
  const actualSeries = [...values, ...Array(f).fill(null)];
  const forecastSeries = f
    ? [...Array(Math.max(n - 1, 0)).fill(null), ...(n > 0 ? [values[n - 1]] : []), ...forecastValues]
    : [];
  const boundaryLabel = labels[n - 1];
  const lastLabel = allLabels[allLabels.length - 1];

  const option = {
    ...baseChartOption,
    grid: { left: 48, right: 16, top: 12, bottom: 40 },
    legend: f
      ? { data: ["Actual", "Forecast"], top: 4, right: 8, textStyle: { color: colors.textMuted, fontSize: 10 } }
      : undefined,
    tooltip: {
      trigger: "axis",
      ...tooltipTheme,
      valueFormatter: (v) => (v === null || v === undefined ? "—" : fmt2(v)),
    },
    xAxis: {
      type: "category",
      data: allLabels,
      ...axisLineTheme,
      ...axisLabelTheme,
      axisLabel: { ...axisLabelTheme.axisLabel, rotate: allLabels.length > 10 ? 45 : 0 },
    },
    yAxis: {
      type: "value",
      ...splitLineTheme,
      ...axisLabelTheme,
      axisLabel: { ...axisLabelTheme.axisLabel, formatter: (v) => fmt2(v) },
    },
    series: [
      {
        name: "Actual",
        data: actualSeries,
        type: "line",
        smooth: true,
        symbol: "circle",
        symbolSize: 5,
        itemStyle: { color: colors.accent },
        lineStyle: { color: colors.accent, width: 2.5 },
        areaStyle: { color: colors.accent, opacity: 0.06 },
        markLine: f
          ? {
              symbol: "none",
              silent: true,
              lineStyle: { color: colors.warn, type: "dashed", width: 1.5 },
              label: { show: true, formatter: "Forecast starts", color: colors.warn, fontSize: 10, position: "insideEndTop" },
              data: [{ xAxis: boundaryLabel }],
            }
          : undefined,
        markArea: f
          ? {
              silent: true,
              itemStyle: { color: colors.warn, opacity: 0.06 },
              data: [[{ xAxis: boundaryLabel }, { xAxis: lastLabel }]],
            }
          : undefined,
      },
      ...(f
        ? [
            {
              name: "Forecast",
              data: forecastSeries,
              type: "line",
              smooth: true,
              symbol: "circle",
              symbolSize: 5,
              itemStyle: { color: colors.warn },
              lineStyle: { color: colors.warn, width: 2, type: "dashed" },
            },
          ]
        : []),
    ],
  };

  const csvData = {
    headers: ["Date", "Actual", "Forecast"],
    rows: allLabels.map((label, i) => [label, actualSeries[i] ?? "", forecastSeries[i] ?? ""]),
  };

  return <ChartCard title={title} option={option} height={260} onRefresh={onRefresh} csvData={csvData} />;
}
