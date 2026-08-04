from app.agents.common import AgentDeps, timed_agent
from app.agents.dimension_explorer import CONTRIBUTION_METRIC

def run(state: dict, deps: AgentDeps) -> dict:
    with timed_agent(state, deps, "EvidenceValidationAgent", {"n_hypotheses": len(state.get("hypotheses", []))}) as rec:
        add_metric = CONTRIBUTION_METRIC[state["metric"]]
        baseline_val = state["_baseline_overall"][add_metric]
        sqls = []
        validated = []
        for h in state.get("hypotheses", []):
            adjusted, sql = deps.repo.overall_excluding_segment(h["dimension"], h["value"], state["target_date"])
            sqls.append(sql)
            adjusted_val = adjusted[add_metric]
            residual_pct = ((adjusted_val - baseline_val) / baseline_val * 100) if baseline_val else 0.0
            is_supported = abs(residual_pct) < deps.settings.significance_threshold_pct
            validated.append({
                **h,
                "is_supported": is_supported,
                "validation_sql": sql,
                "validation_note": (
                    f"Excluding {h['dimension']}={h['value']}, {add_metric} would have been "
                    f"{adjusted_val:.2f} vs baseline {baseline_val:.2f} ({residual_pct:+.1f}% residual). "
                    + ("This explains the anomaly." if is_supported else "A meaningful gap remains - not fully explained by this segment alone.")
                ),
                "residual_after_removal_pct": residual_pct,
            })
        rec["sql_statements"] = sqls
        supported = [v for v in validated if v["is_supported"]]
        rec["reasoning"] = (
            f"{len(supported)}/{len(validated)} hypotheses validated by counterfactual removal."
            if validated else "No hypotheses to validate."
        )
        rec["confidence"] = 0.9 if supported else 0.4
        for v in validated:
            if not v["is_supported"]:
                state.setdefault("ruled_out", []).append(
                    f"{v['dimension']}={v['value']} does not fully explain the anomaly ({v['residual_after_removal_pct']:+.1f}% residual remains)"
                )

        state["validated_hypotheses"] = validated

    return state
