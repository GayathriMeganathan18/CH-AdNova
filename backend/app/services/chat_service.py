from datetime import date, timedelta
from typing import Any
from app.agents.dimension_explorer import RATIO_METRIC_COMPONENTS
from app.observability.llm_client import LLMClient
from app.repositories.clickhouse_repo import DIMENSION_TABLES, ClickHouseRepository
from app.schemas.chat import AnomalyContext, ChatRequest, ChatResponse

SYSTEM_PROMPT = (
    "You are the AI investigation assistant embedded in CH-AdNova, an ad-metrics "
    "root cause investigation platform. Reason ONLY from the numeric evidence "
    "provided in this conversation - never invent metrics, app IDs, regions, "
    "dates, or root causes that aren't supported by that data. If the evidence "
    "doesn't point to a clear cause, say the anomaly appears broad-based rather "
    "than guessing. Keep answers concise and use short markdown-style headers "
    "(**Header**) and bullet points (-) for structured findings."
)

FUNNEL_METRICS: tuple[str, ...] = (
    "requests", "fills", "impressions", "clicks", "revenue", "fill_rate", "ctr", "ecpm",
)


def _avg(rows: list[dict], key: str) -> float | None:
    vals = [r[key] for r in rows if r.get(key) is not None]
    return sum(vals) / len(vals) if vals else None


def _top_movers(
    repo: ClickHouseRepository, dimension: str, target_date: date, baseline_days: int,
    component: str, limit: int = 3,
) -> list[dict[str, Any]]:
    try:
        actual_rows, baseline_rows, _ = repo.dimension_breakdown(dimension, target_date, baseline_days)
    except Exception:
        return []
    key_col = DIMENSION_TABLES[dimension]["key"]
    baseline_by_key = {r.get(key_col): r for r in baseline_rows}
    movers = []
    for row in actual_rows:
        key = row.get(key_col)
        base_row = baseline_by_key.get(key)
        if not base_row or key is None:
            continue
        actual_val = row.get(component) or 0
        baseline_val = base_row.get(component) or 0
        movers.append({
            "key": key, "actual": actual_val, "baseline": baseline_val,
            "delta": actual_val - baseline_val,
        })
    movers.sort(key=lambda m: abs(m["delta"]), reverse=True)
    return movers[:limit]


def gather_anomaly_evidence(
    repo: ClickHouseRepository, anomaly: AnomalyContext, baseline_days: int = 7,
) -> dict[str, Any]:
    """Before/during/after funnel comparison (whole-business daily averages)
    plus real top-moving apps/regions on the anomaly date - everything here
    comes straight out of repo.daily_series/dimension_breakdown, both of
    which already power the dashboard and investigation agents."""
    target = anomaly.target_date
    before_start = target - timedelta(days=3)
    before_end = target - timedelta(days=1)
    after_start = target + timedelta(days=1)
    after_end = target + timedelta(days=1)

    before_rows, _ = repo.daily_series(before_start, before_end)
    during_rows, _ = repo.daily_series(target, target)
    after_rows, _ = repo.daily_series(after_start, after_end)

    comparison = {
        m: {
            "before": _avg(before_rows, m),
            "during": _avg(during_rows, m),
            "after": _avg(after_rows, m),
        }
        for m in FUNNEL_METRICS
    }

    ratio = RATIO_METRIC_COMPONENTS.get(anomaly.metric)
    component = ratio[0] if ratio else (anomaly.metric if anomaly.metric in FUNNEL_METRICS else "revenue")

    return {
        "target_date": str(target),
        "comparison": comparison,
        "top_apps": _top_movers(repo, "app", target, baseline_days, component),
        "top_regions": _top_movers(repo, "region", target, baseline_days, component),
    }


def _fmt(x: float | None) -> str:
    return f"{x:.4f}" if x is not None else "n/a"


def _pct_move(before: float | None, during: float | None) -> float | None:
    if before is None or during is None or before == 0:
        return None
    return (during - before) / before * 100


def _evidence_block_text(evidence: dict[str, Any]) -> str:
    lines = [f"Funnel metrics before / during / after {evidence['target_date']} (daily averages, whole business):"]
    for name, v in evidence["comparison"].items():
        pct = _pct_move(v["before"], v["during"])
        pct_str = f" ({pct:+.1f}% vs before)" if pct is not None else ""
        lines.append(f"- {name}: before={_fmt(v['before'])} during={_fmt(v['during'])} after={_fmt(v['after'])}{pct_str}")

    if evidence.get("top_apps"):
        lines.append("")
        lines.append("Top app-level movers on the anomaly date (vs baseline):")
        for r in evidence["top_apps"]:
            lines.append(f"- app_id={r['key']}: baseline={r['baseline']:.2f} actual={r['actual']:.2f} (delta {r['delta']:+.2f})")

    if evidence.get("top_regions"):
        lines.append("")
        lines.append("Top region-level movers on the anomaly date (vs baseline):")
        for r in evidence["top_regions"]:
            lines.append(f"- region={r['key']}: baseline={r['baseline']:.2f} actual={r['actual']:.2f} (delta {r['delta']:+.2f})")

    return "\n".join(lines)


def build_investigation_kickoff_text(anomaly: AnomalyContext) -> str:
    metric_label = anomaly.metric.replace("_", " ")
    pct = anomaly.baseline.deviation_pct if anomaly.baseline else anomaly.score
    change_line = f"Observed change: {pct:+.1f}%" if pct is not None else "Observed change: n/a"
    lines = [
        "Investigate the following anomaly and determine the most likely root cause.",
        "",
        f"Metric: {metric_label}",
        change_line,
        f"Date: {anomaly.target_date}",
        f"Severity: {anomaly.severity or 'unknown'}",
        "",
        "Analyze related metrics and identify what changed around the anomaly. "
        "Check factors such as requests, fills, impressions, clicks, fill rate, "
        "CTR, eCPM or other relevant metrics available in the system.",
        "",
        "Explain the likely root cause using evidence from the available data.",
    ]
    return "\n".join(lines)


def _fallback_reply(request: ChatRequest, evidence: dict[str, Any] | None) -> str:
    if not evidence:
        return (
            "AI chat isn't connected to a language model right now (no ANTHROPIC_API_KEY "
            "configured), so I can't hold a free-form conversation. Open this from an "
            "anomaly's \"Investigate with AI\" button and I can still show you the "
            "underlying metrics directly."
        )

    target_metric = request.anomaly.metric if request.anomaly else None
    comparison = evidence["comparison"]

    moves = []
    for name, v in comparison.items():
        pct = _pct_move(v["before"], v["during"])
        if pct is not None:
            moves.append((name, pct))
    moves.sort(key=lambda x: abs(x[1]), reverse=True)

    lines = ["**Likely Root Cause**", ""]
    top_other_moves = [m for m in moves if m[0] != target_metric]
    if top_other_moves and abs(top_other_moves[0][1]) >= 5:
        top_name, top_pct = top_other_moves[0]
        subject = target_metric.replace("_", " ").title() if target_metric else "The metric"
        lines.append(
            f"{subject} moved alongside a {top_pct:+.1f}% shift in {top_name.replace('_', ' ')} "
            "over the same window - the strongest correlated signal in the available funnel data."
        )
    else:
        lines.append(
            "No single funnel stage stands out sharply enough to name a confident root cause "
            "from this data alone - the anomaly appears broad-based."
        )

    lines += ["", "**Evidence**", ""]
    for name, pct in moves:
        lines.append(f"- {name.replace('_', ' ').title()}: {pct:+.1f}% vs the prior period")

    affected = []
    for r in evidence.get("top_apps", [])[:3]:
        affected.append(f"- App: {r['key']} (delta {r['delta']:+.2f})")
    for r in evidence.get("top_regions", [])[:3]:
        affected.append(f"- Region: {r['key']} (delta {r['delta']:+.2f})")
    if affected:
        lines += ["", "**Affected Dimensions**", ""] + affected

    lines += [
        "", "**Suggested Next Checks**", "",
        "- Run a full multi-agent investigation from New Investigation for a ranked root cause",
        "- Compare with the previous time period",
        "- Check whether other regions or apps were affected",
    ]
    return "\n".join(lines)


def _llm_reply(llm: LLMClient, request: ChatRequest, evidence: dict[str, Any] | None) -> str:
    system = SYSTEM_PROMPT
    if evidence:
        system = f"{SYSTEM_PROMPT}\n\n{_evidence_block_text(evidence)}"
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    return llm.complete_messages(system=system, messages=messages, max_tokens=700)


def chat_reply(
    repo: ClickHouseRepository, llm: LLMClient, request: ChatRequest, baseline_days: int = 7,
) -> ChatResponse:
    evidence = gather_anomaly_evidence(repo, request.anomaly, baseline_days) if request.anomaly else None

    if llm.enabled:
        try:
            reply = _llm_reply(llm, request, evidence)
            return ChatResponse(reply=reply, used_llm=True, evidence=evidence)
        except Exception:
            pass  

    return ChatResponse(reply=_fallback_reply(request, evidence), used_llm=False, evidence=evidence)
