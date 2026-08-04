import { useCallback, useEffect, useRef, useState } from "react";
import { api, nonEmpty } from "../api/client.js";
import KpiCard from "../components/KpiCard.jsx";
import TrendChart from "../components/TrendChart.jsx";
import DependencyTree from "../components/DependencyTree.jsx";
import CalendarHeatmap from "../components/CalendarHeatmap.jsx";
import TimeSeriesForecastChart from "../components/TimeSeriesForecastChart.jsx";
import SystemHealthWidget from "../components/SystemHealthWidget.jsx";
import LiveAlertsWidget from "../components/LiveAlertsWidget.jsx";
import FilterBar from "../components/FilterBar.jsx";
import { useChartTheme } from "../components/charts/theme.js";
import { SkeletonKpiRow, SkeletonChart } from "../components/ui/Skeleton.jsx";
import ErrorState from "../components/ui/ErrorState.jsx";

const DEFAULT_FILTERS = { timeRange: "30d", customStart: "", customEnd: "", app: "", region: "", publisherTier: "" };
const DAYS_BACK = { "24h": 0, "7d": 6, "30d": 29 };

function dateWindowFor(filters, minDate, maxDate) {
  if (filters.timeRange === "custom") {
    if (!filters.customStart || !filters.customEnd) return null;
    return { start: filters.customStart, end: filters.customEnd };
  }
  const daysBack = DAYS_BACK[filters.timeRange] ?? 29;
  const end = new Date(`${maxDate}T00:00:00`);
  const start = new Date(end);
  start.setDate(start.getDate() - daysBack);
  const startStr = start.toISOString().slice(0, 10);
  return { start: startStr < minDate ? minDate : startStr, end: maxDate };
}

function dimensionFilters(filters) {
  return nonEmpty({ app_id: filters.app, region: filters.region, publisher_tier: filters.publisherTier });
}

async function loadForecast(filters, maxDate, dims) {
  if (filters.timeRange === "custom") {
    if (!filters.customStart || !filters.customEnd) return null;
    const { rows } = await api.dailyMetrics(filters.customStart, filters.customEnd, dims);
    return {
      metric: "revenue",
      window: "custom",
      labels: rows.map((r) => r.day),
      values: rows.map((r) => r.revenue),
      forecast_labels: [],
      forecast_values: [],
    };
  }
  return api.timeseries({ metric: "revenue", target_date: maxDate, window: filters.timeRange, forecast_points: 7, ...dims });
}

export default function Dashboard() {
  const { colors } = useChartTheme();
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [range, setRange] = useState(null);
  const [daily, setDaily] = useState([]);
  const [kpis, setKpis] = useState(null);
  const [depTree, setDepTree] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const requestIdRef = useRef(0);

  const loadAll = useCallback(async (currentFilters, myRequestId) => {
    const r = await api.dateRange();
    if (myRequestId !== requestIdRef.current) return;
    setRange(r);
    if (!r.max_date || !r.min_date) return;

    const window = dateWindowFor(currentFilters, r.min_date, r.max_date);
    const dims = dimensionFilters(currentFilters);
    const [dailyData, kpiData, depTreeData, forecastData] = await Promise.all([
      window ? api.dailyMetrics(window.start, window.end, dims) : Promise.resolve({ rows: [] }),
      api.kpis(r.max_date, 7, dims),
      api.dependencyTree({ target_date: r.max_date, baseline_days: 7 }),
      loadForecast(currentFilters, r.max_date, dims),
    ]);

    if (myRequestId !== requestIdRef.current) return; 
    setDaily(dailyData.rows);
    setKpis(kpiData);
    setDepTree(depTreeData);
    setForecast(forecastData);
  }, []);

  const refresh = useCallback(
    async (currentFilters, { silent = false } = {}) => {
      const myRequestId = ++requestIdRef.current;
      silent ? setRefreshing(true) : setLoading(true);
      setError(null);
      try {
        await loadAll(currentFilters, myRequestId);
      } catch (e) {
        if (myRequestId === requestIdRef.current) setError(e.message || "Failed to load dashboard data");
      } finally {
        if (myRequestId === requestIdRef.current) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    },
    [loadAll]
  );


  const isFirstRun = useRef(true);
  useEffect(() => {
    if (isFirstRun.current) {
      isFirstRun.current = false;
      refresh(filters);
      return;
    }
    const t = setTimeout(() => refresh(filters, { silent: true }), 400);
    return () => clearTimeout(t);
   
  }, [filters.timeRange, filters.customStart, filters.customEnd, filters.app, filters.region, filters.publisherTier]);


  const handleFilterRefresh = () => refresh(filters, { silent: true });

  const refreshDaily = () => refresh(filters, { silent: true });
  const refreshDepTree = async () => {
    if (!range?.max_date) return;
    setDepTree(await api.dependencyTree({ target_date: range.max_date, baseline_days: 7 }));
  };
  const refreshForecast = () => refresh(filters, { silent: true });

  if (error && !loading) {
    return <ErrorState message={`Couldn't load dashboard data: ${error}. Is the backend running and has data been loaded?`} onRetry={() => refresh(filters)} />;
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <SkeletonKpiRow />
        <div className="grid md:grid-cols-3 gap-4">
          <SkeletonChart /><SkeletonChart /><SkeletonChart />
        </div>
        <SkeletonChart height={280} />
      </div>
    );
  }

  const days = daily.map((d) => d.day);

  return (
    <div className={`space-y-6 transition-opacity duration-200 ${refreshing ? "opacity-60" : ""}`}>
      <div className="flex items-end justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-lg font-semibold">Executive KPIs</h2>
          <p className="text-xs text-ink3">Latest date in data: {range.max_date} · vs 7-day baseline</p>
        </div>
      </div>

      <FilterBar value={filters} onChange={setFilters} onRefresh={handleFilterRefresh} refreshing={refreshing} />

      <SystemHealthWidget />

      {kpis && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <KpiCard
            label="Revenue"
            value={kpis.actual.revenue}
            baseline={kpis.baseline.revenue}
            pctChange={((kpis.actual.revenue - kpis.baseline.revenue) / (kpis.baseline.revenue || 1)) * 100}
            sparkline={daily.map((d) => d.revenue)}
          />
          <KpiCard
            label="Requests"
            value={kpis.actual.requests}
            baseline={kpis.baseline.requests}
            pctChange={((kpis.actual.requests - kpis.baseline.requests) / (kpis.baseline.requests || 1)) * 100}
            format={(v) => Math.round(v).toLocaleString()}
            sparkline={daily.map((d) => d.requests)}
          />
          <KpiCard
            label="Fill Rate"
            value={kpis.actual.fill_rate}
            baseline={kpis.baseline.fill_rate}
            pctChange={((kpis.actual.fill_rate - kpis.baseline.fill_rate) / (kpis.baseline.fill_rate || 1)) * 100}
            format={(v) => (v * 100).toFixed(1) + "%"}
            sparkline={daily.map((d) => d.fill_rate)}
          />
          <KpiCard
            label="CTR"
            value={kpis.actual.ctr}
            baseline={kpis.baseline.ctr}
            pctChange={((kpis.actual.ctr - kpis.baseline.ctr) / (kpis.baseline.ctr || 1)) * 100}
            format={(v) => (v * 100).toFixed(2) + "%"}
            sparkline={daily.map((d) => d.ctr)}
          />
          <KpiCard
            label="eCPM"
            value={kpis.actual.ecpm}
            baseline={kpis.baseline.ecpm}
            pctChange={((kpis.actual.ecpm - kpis.baseline.ecpm) / (kpis.baseline.ecpm || 1)) * 100}
            sparkline={daily.map((d) => d.ecpm)}
          />
        </div>
      )}

      <div className="grid md:grid-cols-3 gap-4">
        <TrendChart title="Revenue" days={days} values={daily.map((d) => d.revenue)} color={colors.accent} onRefresh={refreshDaily} />
        <TrendChart title="Fill Rate" days={days} values={daily.map((d) => d.fill_rate)} color={colors.warn} onRefresh={refreshDaily} />
        <TrendChart title="CTR" days={days} values={daily.map((d) => d.ctr)} color={colors.good} onRefresh={refreshDaily} />
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <DependencyTree tree={depTree} onRefresh={refreshDepTree} />
        <LiveAlertsWidget />
      </div>

      <CalendarHeatmap daily={daily} onRefresh={refreshDaily} />

      <TimeSeriesForecastChart
        title={`Revenue — ${filters.timeRange === "custom" ? "Custom Range" : filters.timeRange.toUpperCase() + " Trend + Forecast"}`}
        data={forecast}
        onRefresh={refreshForecast}
      />
    </div>
  );
}
