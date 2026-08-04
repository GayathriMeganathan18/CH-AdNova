def _pct(x) -> str:
    return f"{x:+.1f}%" if x is not None else "—"


def _status(is_abnormal: bool) -> str:
    return "ABNORMAL" if is_abnormal else "normal"


def build_markdown_report(record: dict) -> str:
    lines: list[str] = []
    add = lines.append

    inv_id = record.get("investigation_id", "unknown")
    request = record.get("request", {})
    trigger = record.get("trigger", {})
    overall = trigger.get("overall", {})

    add("# CH-AdNova Incident Report")
    add("")
    add(f"- **Investigation ID:** `{inv_id}`")
    add(f"- **Metric:** {request.get('metric')}")
    add(f"- **Target Date:** {request.get('target_date')}")
    add(f"- **Baseline Days:** {request.get('baseline_days')}")
    add(f"- **Created:** {record.get('created_at', '')}")
    add("")

    add("## Executive Summary")
    add("")
    add("**Anomaly Detected**" if trigger.get("is_anomalous") else "**Within Normal Range**")
    add("")
    add((record.get("executive_summary") or "").strip() or "_No summary generated._")
    add("")
    add(f"Overall confidence: **{round((record.get('overall_confidence') or 0) * 100)}%**")
    if record.get("langfuse_trace_url"):
        add(f"Langfuse trace: {record['langfuse_trace_url']}")
    add("")

    add("## Trigger")
    add("")
    add("| Field | Value |")
    add("|---|---|")
    add(f"| Actual | {overall.get('value')} |")
    add(f"| Baseline | {overall.get('baseline')} |")
    add(f"| Delta | {overall.get('delta')} |")
    add(f"| % Change | {_pct(overall.get('pct_change'))} |")
    add(f"| Reason | {trigger.get('reason', '')} |")
    add("")

    sql_appendix: list[tuple[str, str]] = []  

    funnel_checks = record.get("funnel_checks") or []
    if funnel_checks:
        add("## Funnel Check")
        add("")
        add("| Stage | Baseline | Actual | % Change | Status |")
        add("|---|---|---|---|---|")
        for f in funnel_checks:
            add(f"| {f['stage']} | {f['baseline']:.4f} | {f['actual']:.4f} | {_pct(f['pct_change'])} | {_status(f['is_abnormal'])} |")
        add("")

    funnel_volumes = record.get("funnel_volumes")
    if funnel_volumes:
        add("## Conversion Funnel")
        add("")
        add("| Stage | Volume |")
        add("|---|---|")
        for stage in ("requests", "fills", "impressions", "clicks"):
            if stage in funnel_volumes:
                add(f"| {stage} | {funnel_volumes[stage]:,} |")
        add("")

    explorations = record.get("explorations") or []
    if explorations:
        add("## Dimension Exploration")
        add("")
        for i, exp in enumerate(explorations, 1):
            status = "FLAGGED as significant" if exp.get("is_significant") else "normal"
            add(f"### {i}. {str(exp['dimension']).title()} — {status}")
            add("")
            values = (exp.get("all_values") or [])[:10]
            if values:
                add("| Value | Baseline | Actual | Share of Delta |")
                add("|---|---|---|---|")
                for v in values:
                    add(f"| {v['value']} | {v['baseline_metric']:.2f} | {v['actual_metric']:.2f} | {_pct(v['share_of_total_delta_pct'])} |")
                add("")
            if exp.get("sql"):
                sql_appendix.append((f"DimensionExplorerAgent[{exp['dimension']}]", exp["sql"]))

    drilldowns = record.get("recursive_drilldowns") or []
    if drilldowns:
        add("## Recursive Drilldown")
        add("")
        add("| Depth | Parent Segment | Dimension | Significant | Top Sub-Segment | Share |")
        add("|---|---|---|---|---|---|")
        for d in drilldowns:
            top = d.get("top_contributor") or {}
            add(
                f"| {d['depth']} | {d['parent_dimension']}={d['parent_value']} | {d['dimension']} | "
                f"{'yes' if d['is_significant'] else 'no'} | {top.get('value', '—')} | "
                f"{_pct(top.get('share_of_parent_delta_pct')) if top else '—'} |"
            )
            if d.get("sql"):
                sql_appendix.append((f"RecursiveDrilldownAgent[{d['dimension']}]", d["sql"]))
        add("")

    root_causes = record.get("root_causes") or []
    add("## Root Cause Ranking")
    add("")
    if root_causes:
        for rc in root_causes:
            h = rc["hypothesis"]
            add(f"### #{rc['rank']} — {h['dimension']} = \"{h['value']}\" (confidence {round(rc['confidence'] * 100)}%)")
            add("")
            add(h.get("statement", ""))
            add("")
            add(f"- Business impact: {rc['business_impact_value']:+.2f} ({_pct(rc['business_impact_pct'])})")
            if h.get("validation_note"):
                add(f"- Validation: {h['validation_note']}")
            add("")
            if h.get("validation_sql"):
                sql_appendix.append((f"EvidenceValidationAgent[{h['dimension']}={h['value']}]", h["validation_sql"]))
    else:
        add("_No concentrated root cause found - the anomaly appears broad-based._")
        add("")

    counterfactual = record.get("counterfactual")
    if counterfactual:
        add("## Counterfactual Analysis")
        add("")
        add(counterfactual.get("scenario", ""))
        add("")
        add(f"- Actual: {counterfactual['actual_metric']:.2f}")
        add(f"- Projected: {counterfactual['projected_metric']:.2f}")
        add(f"- Recoverable value: {counterfactual['recovered_value']:+.2f}")
        add("")
        if counterfactual.get("sql"):
            sql_appendix.append(("CounterfactualAgent", counterfactual["sql"]))

    ruled_out = record.get("ruled_out") or []
    if ruled_out:
        add("## Ruled Out")
        add("")
        for r in ruled_out:
            add(f"- {r}")
        add("")

    recommendations = record.get("recommendations") or []
    if recommendations:
        add("## Recommendations")
        add("")
        for r in recommendations:
            add(f"- {r}")
        add("")

    agent_log = record.get("agent_log") or []
    if agent_log:
        add("## Investigation Timeline (Agent Replay)")
        add("")
        add("| # | Agent | Duration (ms) | Confidence | Reasoning |")
        add("|---|---|---|---|---|")
        for i, a in enumerate(agent_log, 1):
            conf = f"{round(a['confidence'] * 100)}%" if a.get("confidence") is not None else "—"
            reasoning = (a.get("reasoning") or "").replace("|", "\\|")
            add(f"| {i} | {a['agent']} | {a['duration_ms']:.2f} | {conf} | {reasoning} |")
            for sql in a.get("sql_statements") or []:
                sql_appendix.append((a["agent"], sql))
        add("")

    if sql_appendix:
        add("## SQL Appendix")
        add("")
        add("Every SQL statement executed during this investigation - the evidence behind every number above.")
        add("")
        seen: set[tuple[str, str]] = set()
        for agent, sql in sql_appendix:
            key = (agent, sql)
            if key in seen:
                continue
            seen.add(key)
            add(f"**{agent}:**")
            add("```sql")
            add(sql.strip())
            add("```")
            add("")

    add("---")
    add(
        "_Generated by CH-AdNova — AI-Powered Root Cause Investigation Platform. "
        "All numeric values above were computed by ClickHouse; narrative text may be "
        "LLM-assisted but never alters or invents a number._"
    )

    return "\n".join(lines)
