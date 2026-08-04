from app.agents.common import AgentDeps, timed_agent

FUNNEL_STAGES = ["requests", "fill_rate", "ctr", "ecpm"]

def run(state: dict, deps: AgentDeps) -> dict:
    with timed_agent(state, deps, "BaselineAnalysisAgent", {"metric": state["metric"]}) as rec:
        actual = state["_actual_overall"]
        baseline = state["_baseline_overall"]
        threshold = deps.settings.significance_threshold_pct
        checks = []
        abnormal_stages = []
        for stage in FUNNEL_STAGES:
            b = baseline[stage]
            a = actual[stage]
            pct = ((a - b) / b * 100) if b else 0.0
            abnormal = abs(pct) >= threshold
            checks.append({
                "stage": stage,
                "baseline": b,
                "actual": a,
                "pct_change": pct,
                "is_abnormal": abnormal,
            })
            if abnormal:
                abnormal_stages.append(stage)
        rec["sql_statements"] = []  
        rec["reasoning"] = (
            f"Funnel check: {', '.join(s['stage'] + (' ABNORMAL' if s['is_abnormal'] else ' normal') for s in checks)}."
            if checks else "No funnel data available."
        )
        rec["confidence"] = 1.0
        state["funnel_checks"] = checks
        state["_abnormal_stages"] = abnormal_stages

    return state
