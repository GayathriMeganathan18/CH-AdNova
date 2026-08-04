from app.agents.common import AgentDeps, timed_agent

TEMPLATE = (
    "{metric} moved primarily because of {dimension} = '{value}', "
    "which went from a baseline of {baseline:.2f} to {actual:.2f} "
    "({share:+.1f}% of the total delta)."
)

def run(state: dict, deps: AgentDeps) -> dict:
    with timed_agent(state, deps, "HypothesisGeneratorAgent", {"n_candidates": len(state.get("attribution", []))}) as rec:
        hypotheses = []
        for i, a in enumerate(state.get("attribution", [])):
            statement = TEMPLATE.format(
                metric=state["metric"], dimension=a["dimension"], value=a["value"],
                baseline=a["baseline_metric"], actual=a["actual_metric"], share=a["share_of_total_delta_pct"],
            )
            if deps.llm.enabled:
                system_prompt = (
                    "You write one crisp, factual sentence explaining an ad-metrics anomaly. "
                    "Use ONLY the numbers given - never invent or recompute any figure."
                )
                user_prompt = (
                    f"Metric: {state['metric']}. Dimension: {a['dimension']}={a['value']}. "
                    f"Baseline: {a['baseline_metric']:.2f}. Actual: {a['actual_metric']:.2f}. "
                    f"Share of total delta: {a['share_of_total_delta_pct']:.1f}%. "
                    "Write one sentence stating this as a hypothesis to be validated."
                )
                try:
                    statement = deps.llm.complete(system=system_prompt, prompt=user_prompt, max_tokens=120)
                    deps.tracer.llm_generation(
                        deps.langfuse_trace, f"HypothesisGeneratorAgent.llm[{i}]", deps.settings.anthropic_model,
                        system_prompt, user_prompt, statement,
                    )
                except Exception as exc:
                    deps.tracer.llm_generation(
                        deps.langfuse_trace, f"HypothesisGeneratorAgent.llm[{i}]", deps.settings.anthropic_model,
                        system_prompt, user_prompt, None, error=str(exc),
                    )

            hypotheses.append({
                "id": f"H{i+1}",
                "statement": statement,
                "dimension": a["dimension"],
                "value": a["value"],
                "supporting_evidence": [
                    f"{a['dimension']}={a['value']} contributed {a['share_of_total_delta_pct']:+.1f}% of the total delta",
                ],
                "delta": a["delta"],
                "share_of_total_delta_pct": a["share_of_total_delta_pct"],
                "baseline_metric": a["baseline_metric"],
                "actual_metric": a["actual_metric"],
            })
        rec["sql_statements"] = []
        rec["reasoning"] = f"Generated {len(hypotheses)} hypothesis/hypotheses from attributed contributors."
        rec["confidence"] = 0.8 if hypotheses else 0.3
        state["hypotheses"] = hypotheses

    return state
