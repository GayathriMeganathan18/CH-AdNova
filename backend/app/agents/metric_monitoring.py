from app.agents.common import AgentDeps, timed_agent


def run(state: dict, deps: AgentDeps) -> dict:
    metric = state["metric"]
    target_date = state["target_date"]
    baseline_days = state["baseline_days"]
    with timed_agent(state, deps, "MetricMonitoringAgent", {"metric": metric, "date": str(target_date)}) as rec:
        actual, actual_sql = deps.repo.overall_daily(target_date)
        baseline, baseline_sql = deps.repo.overall_baseline(target_date, baseline_days)
        rec["sql_statements"] = [actual_sql, baseline_sql]
        actual_val = actual[metric]
        baseline_val = baseline[metric]
        delta = actual_val - baseline_val
        pct_change = (delta / baseline_val * 100) if baseline_val else 0.0
        is_anomalous = abs(pct_change) >= deps.settings.significance_threshold_pct
        rec["reasoning"] = (
            f"{metric} on {target_date} was {actual_val:.2f} vs a {baseline_days}-day "
            f"baseline of {baseline_val:.2f} ({pct_change:+.1f}%). "
            f"{'Exceeds' if is_anomalous else 'Within'} the "
            f"{deps.settings.significance_threshold_pct}% significance threshold."
        )
        rec["confidence"] = 1.0  
        state["trigger"] = {
            "metric": metric,
            "target_date": str(target_date),
            "overall": {
                "value": actual_val,
                "baseline": baseline_val,
                "delta": delta,
                "pct_change": pct_change,
            },
            "is_anomalous": is_anomalous,
            "reason": rec["reasoning"],
        }
        state["_actual_overall"] = actual
        state["_baseline_overall"] = baseline

    return state
