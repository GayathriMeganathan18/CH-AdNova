from app.agents.common import AgentDeps, timed_agent

def run(state: dict, deps: AgentDeps) -> dict:
    with timed_agent(state, deps, "RootCauseRankingAgent", {}) as rec:
        candidates = [v for v in state.get("validated_hypotheses", []) if v["is_supported"]]
        if not candidates:
            candidates = state.get("validated_hypotheses", [])
        baseline_val = state["_baseline_overall"][state["metric"]] if state["metric"] in state["_baseline_overall"] else 0.0
        ranked = []
        for i, c in enumerate(sorted(candidates, key=lambda v: abs(v["delta"]), reverse=True)):
            residual_component = max(0.0, 1 - abs(c["residual_after_removal_pct"]) / 100)
            concentration_component = min(1.0, abs(c["share_of_total_delta_pct"]) / 100)
            confidence = round(0.6 * residual_component + 0.4 * concentration_component, 2)
            confidence = max(0.05, min(confidence, 0.99))
            impact_pct = c["share_of_total_delta_pct"]
            ranked.append({
                "rank": i + 1,
                "hypothesis": c,
                "confidence": confidence,
                "business_impact_value": c["delta"],
                "business_impact_pct": impact_pct,
            })

        rec["sql_statements"] = []
        rec["reasoning"] = (
            f"Ranked {len(ranked)} root cause candidate(s); top: "
            f"{ranked[0]['hypothesis']['dimension']}={ranked[0]['hypothesis']['value']} "
            f"(confidence {ranked[0]['confidence']:.2f})"
            if ranked else "No root cause candidates to rank."
        )
        rec["confidence"] = ranked[0]["confidence"] if ranked else 0.2
        state["root_causes"] = ranked
        state["overall_confidence"] = ranked[0]["confidence"] if ranked else 0.2

    return state
