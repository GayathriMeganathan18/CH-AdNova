from app.agents.common import AgentDeps, timed_agent

def _template_summary(state: dict) -> str:
    trigger = state["trigger"]
    root_causes = state.get("root_causes", [])
    if root_causes:
        top = root_causes[0]
        cause_line = (
            f"The primary driver is {top['hypothesis']['dimension']} = "
            f"'{top['hypothesis']['value']}' (confidence {top['confidence']:.0%}, "
            f"business impact {top['business_impact_value']:+.2f}, "
            f"{top['business_impact_pct']:+.1f}% of the total change)."
        )
    else:
        cause_line = "No single segment concentrated the anomaly - it appears broad-based."
    ruled_out_n = len(state.get("ruled_out", []))
    return (
        f"On {trigger['target_date']}, {trigger['metric']} was {trigger['overall']['value']:.2f} "
        f"against a baseline of {trigger['overall']['baseline']:.2f} "
        f"({trigger['overall']['pct_change']:+.1f}%). {cause_line} "
        f"{ruled_out_n} other dimension(s) were checked and ruled out."
    )


def run(state: dict, deps: AgentDeps) -> dict:
    with timed_agent(state, deps, "ExecutiveSummaryAgent", {}) as rec:
        summary = _template_summary(state)
        if deps.llm.enabled:
            system_prompt = (
                "You write a 2-3 sentence executive summary of an ad-metrics root-cause "
                "investigation for a non-technical business audience. Use ONLY the facts "
                "given - never invent or recompute a number."
            )
            user_prompt = _template_summary(state) + "\n\nRewrite this more naturally for an executive audience, same facts only."
            try:
                summary = deps.llm.complete(system=system_prompt, prompt=user_prompt, max_tokens=250)
                deps.tracer.llm_generation(
                    deps.langfuse_trace, "ExecutiveSummaryAgent.llm", deps.settings.anthropic_model,
                    system_prompt, user_prompt, summary,
                )
            except Exception as exc:
                summary = _template_summary(state)
                deps.tracer.llm_generation(
                    deps.langfuse_trace, "ExecutiveSummaryAgent.llm", deps.settings.anthropic_model,
                    system_prompt, user_prompt, None, error=str(exc),
                )
        rec["sql_statements"] = []
        rec["reasoning"] = "Composed executive summary from finalized root-cause ranking."
        rec["confidence"] = state.get("overall_confidence", 0.5)
        state["executive_summary"] = summary

    return state
