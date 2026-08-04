from app.agents.common import AgentDeps, timed_agent

def run(state: dict, deps: AgentDeps) -> dict:
    with timed_agent(state, deps, "CounterfactualAgent", {}) as rec:
        root_causes = state.get("root_causes", [])
        if not root_causes:
            rec["reasoning"] = "No root cause identified - skipping counterfactual simulation."
            rec["confidence"] = 0.0
            state["counterfactual"] = None
            return state
        top = root_causes[0]["hypothesis"]
        match = next(
            (a for a in state.get("attribution", []) if a["dimension"] == top["dimension"] and a["value"] == top["value"]),
            None,
        )
        if not match:
            rec["reasoning"] = "Could not locate baseline rates for the top root cause - skipping simulation."
            rec["confidence"] = 0.0
            state["counterfactual"] = None
            return state
        result, sql = deps.repo.counterfactual_revenue(
            dimension=top["dimension"],
            value=top["value"],
            target_date=state["target_date"],
            baseline_fill_rate=match["baseline_fill_rate"],
            baseline_ctr=match["baseline_ctr"],
        )
        rec["sql_statements"] = [sql]
        rec["reasoning"] = (
            f"If {top['dimension']}={top['value']} had held its baseline fill rate/CTR, "
            f"revenue would have been ~{result['projected_total_revenue']:.2f} vs actual "
            f"{result['actual_total_revenue']:.2f} - a recoverable ~{result['recovered_value']:.2f}."
        )
        rec["confidence"] = 0.6  # simulation, inherently less certain than direct measurement

        state["counterfactual"] = {
            "scenario": f"{top['dimension']}={top['value']} fill rate/CTR held at baseline",
            "projected_metric": result["projected_total_revenue"],
            "actual_metric": result["actual_total_revenue"],
            "recovered_value": result["recovered_value"],
            "sql": sql,
        }

    return state
