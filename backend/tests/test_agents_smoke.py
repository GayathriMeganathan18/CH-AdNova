from app.agents import (
    metric_monitoring, baseline_analysis, investigation_planner, dimension_explorer,
    recursive_drilldown, metric_attribution, hypothesis_generator, evidence_validation,
    root_cause_ranking, counterfactual, recommendation, executive_summary, trace_agent,
)


def _run_full_chain(base_state, deps):
    state = dict(base_state)
    state = metric_monitoring.run(state, deps)
    state = baseline_analysis.run(state, deps)
    state = investigation_planner.run(state, deps)
    while investigation_planner.route(state, deps) == "explore":
        state = dimension_explorer.run(state, deps)
    state = recursive_drilldown.run(state, deps)
    state = metric_attribution.run(state, deps)
    state = hypothesis_generator.run(state, deps)
    state = evidence_validation.run(state, deps)
    state = root_cause_ranking.run(state, deps)
    state = counterfactual.run(state, deps)
    state = recommendation.run(state, deps)
    state = executive_summary.run(state, deps)
    state = trace_agent.run(state, deps)
    return state


def test_trigger_detects_the_synthetic_drop(base_state, deps):
    state = metric_monitoring.run(dict(base_state), deps)
    assert state["trigger"]["is_anomalous"] is True
    assert state["trigger"]["overall"]["pct_change"] == -20.0


def test_funnel_check_isolates_fill_rate(base_state, deps):
    state = metric_monitoring.run(dict(base_state), deps)
    state = baseline_analysis.run(state, deps)
    abnormal = [c["stage"] for c in state["funnel_checks"] if c["is_abnormal"]]
    assert abnormal == ["fill_rate"]


def test_full_chain_finds_device_as_root_cause(base_state, deps):
    state = _run_full_chain(base_state, deps)
    assert state["dimensions_checked"][0] == "device"  
    assert state["root_causes"], "expected at least one root cause candidate"
    top = state["root_causes"][0]["hypothesis"]
    assert top["dimension"] == "device"
    assert top["value"] == "Galaxy A54"


def test_ruled_out_dimensions_are_recorded(base_state, deps):
    state = _run_full_chain(base_state, deps)
    assert any("normal" in r for r in state["ruled_out"])


def test_counterfactual_is_populated_when_root_cause_found(base_state, deps):
    state = _run_full_chain(base_state, deps)
    assert state["counterfactual"] is not None
    assert state["counterfactual"]["recovered_value"] == 1_500.0


def test_agent_log_has_one_entry_per_agent_invocation(base_state, deps):
    state = _run_full_chain(base_state, deps)
    agent_names = [a["agent"] for a in state["agent_log"]]
    assert agent_names.count("MetricMonitoringAgent") == 1
    assert agent_names.count("DimensionExplorerAgent") >= 1
    assert agent_names[-1] == "LangfuseTraceAgent"
