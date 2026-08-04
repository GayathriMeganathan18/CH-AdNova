from langgraph.graph import StateGraph, START, END
from app.agents import (
    metric_monitoring,
    baseline_analysis,
    investigation_planner,
    dimension_explorer,
    recursive_drilldown,
    metric_attribution,
    hypothesis_generator,
    evidence_validation,
    root_cause_ranking,
    counterfactual,
    recommendation,
    executive_summary,
    trace_agent,
)
from app.agents.common import AgentDeps
from app.agents.state import InvestigationState

def build_graph(deps: AgentDeps):
    graph = StateGraph(InvestigationState)
    graph.add_node("metric_monitoring", lambda s: metric_monitoring.run(s, deps))
    graph.add_node("baseline_analysis", lambda s: baseline_analysis.run(s, deps))
    graph.add_node("investigation_planner", lambda s: investigation_planner.run(s, deps))
    graph.add_node("dimension_explorer", lambda s: dimension_explorer.run(s, deps))
    graph.add_node("recursive_drilldown_agent", lambda s: recursive_drilldown.run(s, deps))
    graph.add_node("metric_attribution", lambda s: metric_attribution.run(s, deps))
    graph.add_node("hypothesis_generator", lambda s: hypothesis_generator.run(s, deps))
    graph.add_node("evidence_validation", lambda s: evidence_validation.run(s, deps))
    graph.add_node("root_cause_ranking", lambda s: root_cause_ranking.run(s, deps))
    graph.add_node("counterfactual_agent", lambda s: counterfactual.run(s, deps))
    graph.add_node("recommendation", lambda s: recommendation.run(s, deps))
    graph.add_node("executive_summary_agent", lambda s: executive_summary.run(s, deps))
    graph.add_node("trace_agent", lambda s: trace_agent.run(s, deps))

    graph.add_edge(START, "metric_monitoring")
    graph.add_edge("metric_monitoring", "baseline_analysis")
    graph.add_edge("baseline_analysis", "investigation_planner")
    graph.add_edge("investigation_planner", "dimension_explorer")

    graph.add_conditional_edges(
        "dimension_explorer",
        lambda s: investigation_planner.route(s, deps),
        {"explore": "dimension_explorer", "done": "recursive_drilldown_agent"},
    )

    graph.add_edge("recursive_drilldown_agent", "metric_attribution")
    graph.add_edge("metric_attribution", "hypothesis_generator")
    graph.add_edge("hypothesis_generator", "evidence_validation")
    graph.add_edge("evidence_validation", "root_cause_ranking")
    graph.add_edge("root_cause_ranking", "counterfactual_agent")
    graph.add_edge("counterfactual_agent", "recommendation")
    graph.add_edge("recommendation", "executive_summary_agent")
    graph.add_edge("executive_summary_agent", "trace_agent")
    graph.add_edge("trace_agent", END)

    return graph.compile()
