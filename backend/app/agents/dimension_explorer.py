from app.agents.common import AgentDeps, timed_agent
from app.repositories.clickhouse_repo import DIMENSION_TABLES

CONTRIBUTION_METRIC = {
    "revenue": "revenue",
    "ecpm": "revenue",
    "requests": "requests",
    "fill_rate": "fills",
    "ctr": "clicks",
    "impressions": "impressions",
    "clicks": "clicks",
}

RATIO_METRIC_COMPONENTS: dict[str, tuple[str, str]] = {
    "fill_rate": ("fills", "requests"),
    "ctr": ("clicks", "impressions"),
    "ecpm": ("revenue", "impressions"),
}

def run(state: dict, deps: AgentDeps) -> dict:
    dim = next(d for d in state["dimensions_to_check"] if d not in state["dimensions_checked"])
    meta_cols = DIMENSION_TABLES[dim]["meta_cols"]
    key_col = DIMENSION_TABLES[dim]["key"]
    metric = state["metric"]
    ratio = RATIO_METRIC_COMPONENTS.get(metric)
    with timed_agent(state, deps, "DimensionExplorerAgent", {"dimension": dim}) as rec:
        actual_rows, baseline_rows, sql = deps.repo.dimension_breakdown(
            dim, state["target_date"], state["baseline_days"]
        )
        rec["sql_statements"] = [sql]
        add_metric = CONTRIBUTION_METRIC[metric]
        total_delta = state["_actual_overall"][add_metric] - state["_baseline_overall"][add_metric]
        baseline_by_key = {row[key_col]: row for row in baseline_rows}
        values = []
        for row in actual_rows:
            key = row[key_col]
            b = baseline_by_key.get(key, {add_metric: 0.0, "fill_rate": 0.0, "ctr": 0.0, "ecpm": 0.0, "requests": 0.0, "fills": 0.0, "impressions": 0.0, "clicks": 0.0, "revenue": 0.0})
            if ratio:
                num, den = ratio
                actual_val = (row.get(num, 0.0) / row[den]) if row.get(den) else 0.0
                baseline_val = (b.get(num, 0.0) / b[den]) if b.get(den) else 0.0
                delta = actual_val - baseline_val
                share = (delta / baseline_val * 100) if baseline_val else 0.0
            else:
                baseline_val = b[add_metric]
                actual_val = row[add_metric]
                delta = actual_val - baseline_val
                share = (delta / total_delta * 100) if total_delta else 0.0

            values.append({
                "dimension": dim,
                "value": key,
                "metadata": {c: row.get(c, "") for c in meta_cols},
                "baseline_metric": baseline_val,
                "actual_metric": actual_val,
                "delta": delta,
                "share_of_total_delta_pct": share,
                "baseline_fill_rate": b.get("fill_rate", 0.0),
                "baseline_ctr": b.get("ctr", 0.0),
            })
        values.sort(key=lambda v: abs(v["share_of_total_delta_pct"] if ratio else v["delta"]), reverse=True)
        top = values[0] if values else None
        threshold = deps.settings.significance_threshold_pct if ratio else deps.settings.concentration_threshold_pct
        is_significant = bool(top and abs(top["share_of_total_delta_pct"]) >= threshold)
        if top and ratio:
            rec["reasoning"] = (
                f"Checked {dim}: top mover is {top['value']} "
                f"({top['share_of_total_delta_pct']:+.1f}% deviation in its own {metric}). "
                f"{'FLAGGED as significant.' if is_significant else 'Within normal spread.'}"
            )
        elif top:
            rec["reasoning"] = (
                f"Checked {dim}: top contributor is {top['value']} "
                f"({top['share_of_total_delta_pct']:+.1f}% of total {add_metric} delta). "
                f"{'FLAGGED as significant.' if is_significant else 'Within normal spread.'}"
            )
        else:
            rec["reasoning"] = f"Checked {dim}: no rows found for this date."
        rec["confidence"] = 0.9 if is_significant else 0.6

        exploration = {
            "dimension": dim,
            "is_significant": is_significant,
            "top_contributor": top,
            "all_values": values[:20],  
            "sql": sql,
        }
        state["explorations"].append(exploration)
        state["dimensions_checked"].append(dim)
        if is_significant:
            state["flagged_dimensions"].append(exploration)
        else:
            state.setdefault("ruled_out", []).append(
                f"{dim} normal (top mover {top['value']} only {top['share_of_total_delta_pct']:+.1f}% deviation)"
                if top else f"{dim} normal (no data)"
            )

    return state
