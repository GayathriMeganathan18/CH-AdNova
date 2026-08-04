import ReactECharts from "echarts-for-react";
import { useChartTheme } from "./charts/theme.js";

export default function ConfidenceGauge({ confidence = 0, size = 160 }) {
  const { colors } = useChartTheme();
  const pct = Math.round(confidence * 100);
  const color = pct >= 70 ? colors.good : pct >= 40 ? colors.warn : colors.bad;

  const option = {
    series: [
      {
        type: "gauge",
        startAngle: 210,
        endAngle: -30,
        min: 0,
        max: 100,
        splitNumber: 5,
        itemStyle: { color },
        progress: { show: true, width: 12 },
        pointer: { show: false },
        axisLine: { lineStyle: { width: 12, color: [[1, colors.gridLine]] } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        detail: {
          valueAnimation: true,
          formatter: "{value}%",
          color: colors.textPrimary,
          fontSize: 22,
          offsetCenter: [0, "0%"],
        },
        data: [{ value: pct }],
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: size, width: size }} notMerge />;
}
