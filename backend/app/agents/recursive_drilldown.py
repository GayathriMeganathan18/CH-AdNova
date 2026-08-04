from app.agents.common import AgentDeps, timed_agent
from app.agents.dimension_explorer import CONTRIBUTION_METRIC, RATIO_METRIC_COMPONENTS
from app.repositories.clickhouse_repo import DIMENSION_TABLES

MAX_DEPTH = 2
SECONDARY_DIMENSIONS: dict[str, list[str]] = {
    "geo": ["device", "os", "publisher"],
    "region": ["device", "os", "publisher"],
    "device": ["geo", "os", "app"],
    "os": ["geo", "device", "app"],
    "app": ["geo", "device", "publisher"],
    "advertiser": ["geo", "format", "app"],
    "format": ["geo", "device", "app"],
    "publisher": ["geo", "device", "app"],
}

def _drill_one_level(deps, target_date, baseline_days, metric, add_metric, parent_dimension, parent_value, parent_delta, visited):
    ratio = RATIO_METRIC_COMPONENTS.get(metric)
    findings = []
    for child_dim in SECONDARY_DIMENSIONS.get(parent_dimension, []):
        if child_dim in visited:
            continue
        key_col = DIMENSION_TABLES[child_dim]["key"]
        actual_rows, baseline_rows, sql = deps.repo.filtered_dimension_breakdown(
            child_dim, target_date, baseline_days,
            filter_column=DIMENSION_TABLES[parent_dimension]["key"], filter_value=parent_value,
        )
        baseline_by_key = {row[key_col]: row for row in baseline_rows}
        values = []
        for row in actual_rows:
            key = row[key_col]
            if ratio:
                num, den = ratio
                b = baseline_by_key.get(key, {num: 0.0, den: 0.0})
                actual_val = (row.get(num, 0.0) / row[den]) if row.get(den) else 0.0
                baseline_val = (b.get(num, 0.0) / b[den]) if b.get(den) else 0.0
                delta = actual_val - baseline_val
                # this segment's own rate deviation from its own baseline -
                # same reasoning as DimensionExplorerAgent's ratio-metric path
                share = (delta / baseline_val * 100) if baseline_val else 0.0
            else:
                b = baseline_by_key.get(key, {add_metric: 0.0})
                baseline_val = b.get(add_metric, 0.0)
                actual_val = row.get(add_metric, 0.0)
                delta = actual_val - baseline_val
                share = (delta / parent_delta * 100) if parent_delta else 0.0
            values.append({
                "dimension": child_dim,
                "value": key,
                "baseline_metric": baseline_val,
                "actual_metric": actual_val,
                "delta": delta,
                "share_of_parent_delta_pct": share,
            })
        values.sort(key=lambda v: abs(v["share_of_parent_delta_pct"] if ratio else v["delta"]), reverse=True)
        top = values[0] if values else None
        threshold = deps.settings.significance_threshold_pct if ratio else deps.settings.concentration_threshold_pct
        is_significant = bool(top and abs(top["share_of_parent_delta_pct"]) >= threshold)
        findings.append({
            "parent_dimension": parent_dimension,
            "parent_value": parent_value,
            "dimension": child_dim,
            "is_significant": is_significant,
            "top_contributor": top,
            "all_values": values[:10],
            "sql": sql,
        })
    return findings

def run(state: dict, deps: AgentDeps) -> dict:
    flagged = state.get("flagged_dimensions", [])
    with timed_agent(state, deps, "RecursiveDrilldownAgent", {"flagged_count": len(flagged)}) as rec:
        metric = state["metric"]
        add_metric = CONTRIBUTION_METRIC[metric]
        drilldowns: list[dict] = []
        sql_statements: list[str] = []
        for f in flagged:
            top = f.get("top_contributor")
            if not top:
                continue
            parent_dim, parent_value, parent_delta = f["dimension"], top["value"], top["delta"]
            visited = {parent_dim}
            frontier = [(parent_dim, parent_value, parent_delta)]
            depth = 1
            while frontier and depth <= MAX_DEPTH:
                next_frontier = []
                for p_dim, p_value, p_delta in frontier:
                    level_findings = _drill_one_level(
                        deps, state["target_date"], state["baseline_days"], metric, add_metric,
                        p_dim, p_value, p_delta, visited,
                    )
                    for lf in level_findings:
                        sql_statements.append(lf["sql"])
                        drilldowns.append({**lf, "depth": depth})
                        if lf["is_significant"] and lf["top_contributor"]:
                            visited.add(lf["dimension"])
                            next_frontier.append(
                                (lf["dimension"], lf["top_contributor"]["value"], lf["top_contributor"]["delta"])
                            )
                frontier = next_frontier
                depth += 1
        significant_count = sum(1 for d in drilldowns if d["is_significant"])
        rec["sql_statements"] = sql_statements
        rec["reasoning"] = (
            f"Drilled into {len(flagged)} flagged dimension(s); found {significant_count} further-concentrated sub-segment(s)."
            if flagged else "No dimension was flagged as significant - nothing to drill into."
        )
        rec["confidence"] = 0.7 if significant_count else (0.3 if flagged else 0.5)
        state["recursive_drilldowns"] = drilldowns

    return state
