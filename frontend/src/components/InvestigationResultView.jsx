import FunnelChecklist from "./FunnelChecklist.jsx";
import DimensionExplorationPanel from "./DimensionExplorationPanel.jsx";
import RuledOutList from "./RuledOutList.jsx";
import RootCauseList from "./RootCauseList.jsx";
import CounterfactualCard from "./CounterfactualCard.jsx";
import RecommendationsPanel from "./RecommendationsPanel.jsx";
import AgentTimeline from "./AgentTimeline.jsx";
import FunnelChart from "./FunnelChart.jsx";
import DrilldownSunburst from "./DrilldownSunburst.jsx";
import ViewClickStackButton from "./ViewClickStackButton.jsx";

export default function InvestigationResultView({ result }) {
  if (!result) return null;
  const {
    trigger, funnel_checks, funnel_volumes, explorations, recursive_drilldowns, ruled_out, root_causes,
    counterfactual, recommendations, executive_summary, overall_confidence, agent_log, langfuse_trace_url,
  } = result;

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-br from-accent/10 to-transparent border border-accent/20 rounded-xl p-5">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs uppercase tracking-wide text-ink3">Executive Summary</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${trigger.is_anomalous ? "bg-bad/20 text-bad" : "bg-good/20 text-good"}`}>
            {trigger.is_anomalous ? "Anomaly Detected" : "Within Normal Range"}
          </span>
        </div>
        <p className="text-ink">{executive_summary}</p>
        <div className="flex items-center gap-4 mt-3 text-xs text-ink3">
          <span>Overall confidence: {(overall_confidence * 100).toFixed(0)}%</span>
          {langfuse_trace_url && (
            <a href={langfuse_trace_url} target="_blank" rel="noreferrer" className="text-accent hover:underline">
              View Langfuse trace ↗
            </a>
          )}
          <ViewClickStackButton variant="link" />
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <FunnelChecklist checks={funnel_checks} />
        <RuledOutList items={ruled_out} />
      </div>

      {funnel_volumes && <FunnelChart volumes={funnel_volumes} />}

      <DimensionExplorationPanel explorations={explorations} />

      {recursive_drilldowns?.length > 0 && <DrilldownSunburst drilldowns={recursive_drilldowns} />}

      <RootCauseList rootCauses={root_causes} />

      <div className="grid md:grid-cols-2 gap-4">
        <CounterfactualCard counterfactual={counterfactual} />
        <RecommendationsPanel recommendations={recommendations} />
      </div>

      <AgentTimeline agentLog={agent_log} />
    </div>
  );
}
