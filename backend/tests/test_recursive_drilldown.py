import pytest
from app.agents import dimension_explorer, recursive_drilldown


def _flag_device(base_state):
    state = dict(base_state)
    state.update({
        "dimensions_to_check": ["device"],
        "dimensions_checked": [],
        "explorations": [],
        "flagged_dimensions": [],
        "ruled_out": [],
        "_actual_overall": {"revenue": 8_000.0, "requests": 100_000, "fills": 40_000, "impressions": 38_000, "clicks": 760},
        "_baseline_overall": {"revenue": 10_000.0, "requests": 100_000, "fills": 50_000, "impressions": 48_000, "clicks": 960},
    })
    return state


def test_flagging_precondition_holds(base_state, deps):
    state = dimension_explorer.run(_flag_device(base_state), deps)
    assert len(state["flagged_dimensions"]) == 1
    assert state["flagged_dimensions"][0]["dimension"] == "device"
    assert state["flagged_dimensions"][0]["top_contributor"]["value"] == "Galaxy A54"
    assert state["flagged_dimensions"][0]["top_contributor"]["delta"] == -2_000.0


def test_recursive_drilldown_finds_concentrated_sub_segment(base_state, deps):
    state = dimension_explorer.run(_flag_device(base_state), deps)
    state = recursive_drilldown.run(state, deps)

    findings = state["recursive_drilldowns"]
    assert findings

    geo_finding = next(f for f in findings if f["dimension"] == "geo" and f["parent_dimension"] == "device")
    assert geo_finding["parent_value"] == "Galaxy A54"
    assert geo_finding["is_significant"] is True
    assert geo_finding["top_contributor"]["value"] == "IN"
    assert geo_finding["top_contributor"]["share_of_parent_delta_pct"] == pytest.approx(70.0)
    assert geo_finding["sql"]  
   
    other_children = [f for f in findings if f["depth"] == 1 and f["dimension"] != "geo"]
    assert {f["dimension"] for f in other_children} == {"os", "app"}
    assert all(not f["is_significant"] for f in other_children)


def test_recursive_drilldown_goes_one_level_deeper_from_a_significant_find(base_state, deps):
    state = dimension_explorer.run(_flag_device(base_state), deps)
    state = recursive_drilldown.run(state, deps)
    depth_2 = [f for f in state["recursive_drilldowns"] if f["depth"] == 2]
    assert depth_2
    assert all(f["parent_dimension"] == "geo" and f["parent_value"] == "IN" for f in depth_2)


def test_recursive_drilldown_does_not_revisit_the_flagged_dimension(base_state, deps):
    state = dimension_explorer.run(_flag_device(base_state), deps)
    state = recursive_drilldown.run(state, deps)
    assert not any(f["dimension"] == "device" for f in state["recursive_drilldowns"])


def test_recursive_drilldown_is_a_noop_when_nothing_was_flagged(base_state, deps):
    state = dict(base_state)
    state["flagged_dimensions"] = []
    state["agent_log"] = []
    state = recursive_drilldown.run(state, deps)
    assert state["recursive_drilldowns"] == []
