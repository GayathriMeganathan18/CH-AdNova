from app.agents.common import AgentDeps, timed_agent

DIMENSION_PLAYBOOK: dict[str, list[str]] = {
    "app": [
        "Audit the flagged app's ad unit placement and SDK integration for the affected date.",
        "Check for a recent app version release or ad unit configuration change.",
    ],
    "advertiser": [
        "Contact the flagged advertiser/campaign manager to confirm budget pacing or targeting changes.",
        "Check for campaign pause, budget exhaustion, or creative disapproval on that date.",
    ],
    "geo": [
        "Check for regional regulatory, connectivity, or demand-side platform outages in the flagged country/region.",
        "Verify local currency/exchange-rate handling if revenue (not just volume) is affected.",
    ],
    "device": [
        "Check for an OS/device-specific SDK compatibility issue or a recent OS update in the flagged segment.",
        "Compare mediation waterfall fill behavior for this device/OS combination against other segments.",
    ],
    "format": [
        "Check for a demand-side issue specific to the flagged ad format (e.g. video vs banner fill).",
        "Review recent format-level configuration or floor-price changes.",
    ],
}

def run(state: dict, deps: AgentDeps) -> dict:
    with timed_agent(state, deps, "RecommendationAgent", {}) as rec:
        root_causes = state.get("root_causes", [])
        recommendations: list[str] = []
        for rc in root_causes[:3]:
            dim = rc["hypothesis"]["dimension"]
            recommendations.extend(DIMENSION_PLAYBOOK.get(dim, []))
        if not recommendations:
            recommendations = [
                "No single segment explains the anomaly - review for a platform-wide cause "
                "(e.g. tracking/measurement change, broad demand shift, or seasonal pattern) "
                "rather than a localized one."
            ]
        rec["sql_statements"] = []
        rec["reasoning"] = f"Produced {len(recommendations)} recommendation(s) from the top {min(3, len(root_causes))} root cause(s)."
        rec["confidence"] = 0.7 if root_causes else 0.3
        state["recommendations"] = recommendations

    return state
