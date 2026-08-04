import axios from "axios";

// In production (Vercel), there's no reverse proxy to make a relative
// "/api" path resolve anywhere - VITE_API_BASE_URL must point directly at
// the deployed backend, e.g. https://ch-adnova-backend.onrender.com/api.
// Left unset (local Docker/dev), both fall back to the relative paths
// nginx (or Vite's dev proxy) already handles.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
const ROOT_BASE_URL = API_BASE_URL.replace(/\/api\/?$/, "") || "/";

const client = axios.create({ baseURL: API_BASE_URL });
const rootClient = axios.create({ baseURL: ROOT_BASE_URL });
export function nonEmpty(obj = {}) {
  return Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== undefined && v !== null && v !== ""));
}

export const api = {
  dateRange: () => client.get("/metrics/date-range").then((r) => r.data),
  dailyMetrics: (start, end, dimensionFilters = {}) =>
    client.get("/metrics/daily", { params: { start, end, ...nonEmpty(dimensionFilters) } }).then((r) => r.data),
  kpis: (targetDate, baselineDays = 7, dimensionFilters = {}) =>
    client
      .get("/metrics/kpis", {
        params: { target_date: targetDate, baseline_days: baselineDays, ...nonEmpty(dimensionFilters) },
      })
      .then((r) => r.data),
  investigate: (payload) => client.post("/investigate", payload).then((r) => r.data),
  getInvestigation: (id) => client.get(`/investigations/${id}`).then((r) => r.data),
  listInvestigations: () => client.get("/investigations").then((r) => r.data),
  health: () => rootClient.get("/health").then((r) => r.data),

  
  analyticsStrategies: () => client.get("/analytics/strategies").then((r) => r.data),
  baseline: (params) => client.get("/analytics/baseline", { params }).then((r) => r.data),
  anomalyCheck: (params) => client.get("/analytics/anomaly", { params }).then((r) => r.data),
  dependencyTree: (params) => client.get("/analytics/dependency-tree", { params }).then((r) => r.data),

  
  listAlerts: (params) => client.get("/analytics/alerts", { params }).then((r) => r.data),
  monitorStatus: () => client.get("/monitor/status").then((r) => r.data),
  runMonitorNow: () => client.post("/monitor/run-now").then((r) => r.data),

  
  timeseries: (params) => client.get("/analytics/timeseries", { params }).then((r) => r.data),
  systemHealth: () => client.get("/system/health").then((r) => r.data),

  exportUrl: (id, format) => `/api/investigations/${id}/export?format=${format}`,

  chat: (payload) => client.post("/chat", payload).then((r) => r.data),
};
