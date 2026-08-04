import { useMemo } from "react";
import { useTheme } from "../../theme/ThemeContext.jsx";

const DARK_COLORS = {
  accent: "#38bdf8",
  good: "#34d399",
  warn: "#fbbf24",
  bad: "#f87171",
  panel: "#12161c",
  panel2: "#1a1f27",
  border: "#2a3140",
  gridLine: "#1e2530",
  textPrimary: "#e2e8f0",
  textSecondary: "#cbd5e1",
  textMuted: "#64748b",
};

const LIGHT_COLORS = {
  accent: "#0284c7",
  good: "#059669",
  warn: "#b45309",
  bad: "#dc2626",
  panel: "#ffffff",
  panel2: "#ffffff",
  border: "rgba(15, 23, 42, 0.14)",
  gridLine: "rgba(15, 23, 42, 0.08)",
  textPrimary: "#0f172a",
  textSecondary: "#334155",
  textMuted: "#64748b",
};

export function getChartColors(resolvedTheme) {
  return resolvedTheme === "light" ? LIGHT_COLORS : DARK_COLORS;
}

export const CHART_COLORS = DARK_COLORS;
export const baseChartOption = { backgroundColor: "transparent" };
export const chartPanelClass = "bg-panel2 border border-line rounded-xl themed-transition";
export function labelFor(name) {
  return String(name).replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function useChartTheme() {
  const { resolvedTheme } = useTheme();
  return useMemo(() => {
    const colors = getChartColors(resolvedTheme);
    return {
      resolvedTheme,
      colors,
      SEVERITY_COLOR: { none: colors.good, low: colors.warn, medium: colors.warn, high: colors.bad },
      NAMED_COLOR: { green: colors.good, amber: colors.warn, red: colors.bad },
      baseChartOption,
      tooltipTheme: {
        backgroundColor: colors.panel2,
        borderColor: colors.border,
        borderWidth: 1,
        padding: [10, 14],
        textStyle: { color: colors.textPrimary, fontSize: 12, lineHeight: 18 },
        extraCssText: "box-shadow: 0 8px 24px rgba(0,0,0,0.16); border-radius: 8px;",
      },
      axisLineTheme: { axisLine: { lineStyle: { color: colors.border } } },
      axisLabelTheme: { axisLabel: { color: colors.textMuted, fontSize: 10 } },
      splitLineTheme: { splitLine: { lineStyle: { color: colors.gridLine } } },
    };
  }, [resolvedTheme]);
}
