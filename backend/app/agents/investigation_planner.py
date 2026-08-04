from app.agents.common import AgentDeps, timed_agent
from app.agents.state import DIMENSION_ORDER

STAGE_DIMENSION_PRIORITY: dict[str, list[str]] = {
    "requests":  ["app", "geo", "device", "advertiser", "format"],
    "fill_rate": ["device", "geo", "advertiser", "app", "format"],
    "ctr":       ["app", "format", "device", "geo", "advertiser"],
    "ecpm":      ["advertiser", "format", "app", "geo", "device"],
}

def run(state: dict, deps: AgentDeps) -> dict:
    with timed_agent(state, deps, "InvestigationPlannerAgent", {"abnormal_stages": state.get("_abnormal_stages", [])}) as rec:
        abnormal_stages = state.get("_abnormal_stages", [])
        if not abnormal_stages:
            order = list(DIMENSION_ORDER)
            rec["reasoning"] = "No single funnel stage was individually abnormal; using default dimension order."
        else:
            order = []
            for stage in abnormal_stages:
                for dim in STAGE_DIMENSION_PRIORITY.get(stage, DIMENSION_ORDER):
                    if dim not in order:
                        order.append(dim)
            for dim in DIMENSION_ORDER:
                if dim not in order:
                    order.append(dim)
            rec["reasoning"] = (
                f"Funnel stages abnormal: {', '.join(abnormal_stages)}. "
                f"Prioritizing dimension check order: {' -> '.join(order)}."
            )

        rec["confidence"] = 0.8
        state["dimensions_to_check"] = order
        state["dimensions_checked"] = []
        state["explorations"] = []
        state["flagged_dimensions"] = []

    return state


def route(state: dict, deps: AgentDeps) -> str:
    """
    Conditional edge function: called after each DimensionExplorerAgent run.
    Returns "explore" to keep going or "done" to move on to attribution.
    """
    remaining = [d for d in state["dimensions_to_check"] if d not in state["dimensions_checked"]]
    if not remaining:
        return "done"

    flagged = state.get("flagged_dimensions", [])
    checked_count = len(state["dimensions_checked"])
    strong_signal = any(
        f["top_contributor"]["share_of_total_delta_pct"] >= deps.settings.concentration_threshold_pct * 1.5
        for f in flagged
    )
    if checked_count >= 2 and strong_signal:
        return "done"

    return "explore"
