/**
 * Shared JSDoc typedefs for the "Investigate with AI" chat feature. Plain JS
 * project (no TypeScript build step) - these exist for editor
 * intellisense/documentation, mirroring the real shapes the backend
 * schemas (app/schemas/chat.py) accept.
 *
 * @typedef {Object} AnomalyInvestigationContext
 * Real anomaly record from GET /api/analytics/alerts (AnomalyStore). No
 * app_id/region/publisher_tier field exists here on purpose: anomalies are
 * detected at the overall-metric level, not scoped to a dimension - that
 * attribution only ever exists inside a completed investigation's
 * root_causes. Only id/metric/target_date are guaranteed present.
 * @property {string} id
 * @property {string} metric
 * @property {string} target_date
 * @property {string} [severity]
 * @property {number} [score]
 * @property {string} [strategy]
 * @property {number} [threshold]
 * @property {{expected:number, actual:number, deviation:number, deviation_pct:number, severity?:string, confidence?:number}} [baseline]
 * @property {string} [detected_at]
 * @property {string} [status]
 * @property {string} [source]
 * @property {string} [investigation_id]
 * @property {string} [root_cause_summary]
 * @property {string} [executive_summary]
 */

/**
 * @typedef {Object} ChatMessage
 * @property {"user"|"assistant"} role
 * @property {string} content
 */

/**
 * @typedef {Object} ChatNavigationState
 * Shape passed via navigate("/chat", { state }) from "Investigate with AI".
 * @property {"anomaly-investigation"} mode
 * @property {AnomalyInvestigationContext} anomaly
 */

export {};
