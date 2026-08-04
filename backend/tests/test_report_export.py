from app.services.report_export import build_markdown_report

FULL_RECORD = {
    "investigation_id": "inv-123",
    "request": {"metric": "revenue", "target_date": "2026-06-18", "baseline_days": 7},
    "trigger": {
        "metric": "revenue", "target_date": "2026-06-18",
        "overall": {"value": 456.92, "baseline": 512.71, "delta": -55.79, "pct_change": -10.9},
        "is_anomalous": True, "reason": "revenue dropped 10.9%",
    },
    "funnel_checks": [
        {"stage": "requests", "baseline": 210786.0, "actual": 187788.0, "pct_change": -10.9, "is_abnormal": True},
        {"stage": "fill_rate", "baseline": 1.0, "actual": 1.0, "pct_change": 0.0, "is_abnormal": False},
    ],
    "funnel_volumes": {"requests": 187788, "fills": 187788, "impressions": 183000, "clicks": 2000},
    "explorations": [
        {
            "dimension": "device", "is_significant": True,
            "top_contributor": {"dimension": "device", "value": "Galaxy A54", "baseline_metric": 3000.0, "actual_metric": 1000.0, "delta": -2000.0, "share_of_total_delta_pct": 100.0},
            "all_values": [{"dimension": "device", "value": "Galaxy A54", "baseline_metric": 3000.0, "actual_metric": 1000.0, "delta": -2000.0, "share_of_total_delta_pct": 100.0}],
            "sql": "SELECT ... by_device",
        },
    ],
    "recursive_drilldowns": [
        {
            "depth": 1, "parent_dimension": "device", "parent_value": "Galaxy A54", "dimension": "geo",
            "is_significant": True,
            "top_contributor": {"dimension": "geo", "value": "IN", "baseline_metric": 2000.0, "actual_metric": 600.0, "delta": -1400.0, "share_of_parent_delta_pct": 70.0},
            "all_values": [], "sql": "SELECT ... filtered_geo_within_device",
        },
    ],
    "ruled_out": ["ctr normal (deviation 0.4%)"],
    "root_causes": [
        {
            "rank": 1,
            "hypothesis": {
                "id": "H1", "statement": "device=Galaxy A54 driven by IN", "dimension": "device", "value": "Galaxy A54",
                "supporting_evidence": [], "is_supported": True,
                "validation_sql": "SELECT ... excluding_segment", "validation_note": "removing it restores baseline",
                "residual_after_removal_pct": 2.0,
            },
            "confidence": 0.85, "business_impact_value": -2000.0, "business_impact_pct": 100.0,
        },
    ],
    "counterfactual": {
        "scenario": "Galaxy A54 fill rate held at baseline", "projected_metric": 9500.0,
        "actual_metric": 8000.0, "recovered_value": 1500.0, "sql": "SELECT ... counterfactual",
    },
    "recommendations": ["Investigate Galaxy A54 fill rate in India."],
    "executive_summary": "Revenue dropped 10.9% on 2026-06-18, concentrated in Galaxy A54 devices in India.",
    "overall_confidence": 0.85,
    "agent_log": [
        {"agent": "MetricMonitoringAgent", "started_at": "2026-06-18T00:00:00Z", "duration_ms": 12.3, "sql_statements": ["SELECT ... overall_daily"], "reasoning": "revenue dropped", "confidence": 1.0},
    ],
    "langfuse_trace_url": "http://langfuse:3000/trace/inv-123",
    "created_at": "2026-06-18T12:00:00Z",
}


def test_report_includes_every_major_section():
    md = build_markdown_report(FULL_RECORD)
    for heading in [
        "# CH-AdNova Incident Report", "## Executive Summary", "## Trigger", "## Funnel Check",
        "## Conversion Funnel", "## Dimension Exploration", "## Recursive Drilldown",
        "## Root Cause Ranking", "## Counterfactual Analysis", "## Ruled Out",
        "## Recommendations", "## Investigation Timeline (Agent Replay)", "## SQL Appendix",
    ]:
        assert heading in md, f"missing section: {heading}"


def test_report_never_fabricates_numbers_it_just_formats_them():
    md = build_markdown_report(FULL_RECORD)
    assert "456.92" in md
    assert "Galaxy A54" in md
    assert "-2000.00" in md or "-2,000.00" in md or "-2000.0" in md


def test_report_sql_appendix_deduplicates():
    record = dict(FULL_RECORD)
    record["agent_log"] = [
        {"agent": "A", "started_at": "x", "duration_ms": 1.0, "sql_statements": ["SELECT 1"], "reasoning": "r", "confidence": 1.0},
        {"agent": "A", "started_at": "x", "duration_ms": 1.0, "sql_statements": ["SELECT 1"], "reasoning": "r2", "confidence": 1.0},
    ]
    md = build_markdown_report(record)
    assert md.count("SELECT 1") == 1


def test_report_handles_missing_optional_fields_gracefully():
    minimal = {
        "investigation_id": "inv-min",
        "request": {"metric": "revenue", "target_date": "2026-01-01", "baseline_days": 7},
        "trigger": {"metric": "revenue", "target_date": "2026-01-01", "overall": {}, "is_anomalous": False, "reason": ""},
        "funnel_checks": [], "explorations": [], "ruled_out": [], "root_causes": [],
        "counterfactual": None, "recommendations": [], "executive_summary": "",
        "overall_confidence": 0.0, "agent_log": [], "created_at": "2026-01-01T00:00:00Z",
    }
    md = build_markdown_report(minimal)  # must not raise
    assert "# CH-AdNova Incident Report" in md
    assert "No concentrated root cause" in md


def test_report_no_root_cause_case_is_explicit():
    record = dict(FULL_RECORD)
    record["root_causes"] = []
    md = build_markdown_report(record)
    assert "No concentrated root cause found" in md
