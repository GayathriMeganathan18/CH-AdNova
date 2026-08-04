from dataclasses import replace
from app.agents import executive_summary, hypothesis_generator
from conftest import FailingFakeLLM, WorkingFakeLLM


def _state_with_attribution(base_state):
    state = dict(base_state)
    state["attribution"] = [{
        "dimension": "device", "value": "Galaxy A54",
        "baseline_metric": 3000.0, "actual_metric": 1000.0,
        "delta": -2000.0, "share_of_total_delta_pct": 100.0,
    }]
    return state


def test_hypothesis_generator_logs_a_generation_on_success(base_state, deps):
    deps = replace(deps, llm=WorkingFakeLLM())
    state = hypothesis_generator.run(_state_with_attribution(base_state), deps)

    assert state["hypotheses"][0]["statement"].startswith("fake completion")
    assert len(deps.tracer.generations) == 1
    name, model, system, prompt, completion, error = deps.tracer.generations[0]
    assert name == "HypothesisGeneratorAgent.llm[0]"
    assert completion is not None
    assert error is None


def test_hypothesis_generator_falls_back_and_logs_the_error_on_llm_failure(base_state, deps):
    deps = replace(deps, llm=FailingFakeLLM())
    state = hypothesis_generator.run(_state_with_attribution(base_state), deps)
    assert "device" in state["hypotheses"][0]["statement"]
    assert len(deps.tracer.generations) == 1
    _, _, _, _, completion, error = deps.tracer.generations[0]
    assert completion is None
    assert "simulated LLM outage" in error


def test_executive_summary_logs_a_generation_on_success(base_state, deps):
    deps = replace(deps, llm=WorkingFakeLLM())
    state = dict(base_state)
    state["trigger"] = {"target_date": "2026-01-15", "metric": "revenue", "overall": {"value": 100.0, "baseline": 120.0, "pct_change": -16.7}}
    state["root_causes"] = []
    state["ruled_out"] = []
    state["overall_confidence"] = 0.5
    state = executive_summary.run(state, deps)
    assert state["executive_summary"].startswith("fake completion")
    assert len(deps.tracer.generations) == 1
    assert deps.tracer.generations[0][4] is not None  # completion


def test_executive_summary_falls_back_and_logs_the_error_on_llm_failure(base_state, deps):
    deps = replace(deps, llm=FailingFakeLLM())
    state = dict(base_state)
    state["trigger"] = {"target_date": "2026-01-15", "metric": "revenue", "overall": {"value": 100.0, "baseline": 120.0, "pct_change": -16.7}}
    state["root_causes"] = []
    state["ruled_out"] = []
    state["overall_confidence"] = 0.5

    state = executive_summary.run(state, deps)

    assert "On 2026-01-15" in state["executive_summary"]  # template fallback, not a crash
    assert len(deps.tracer.generations) == 1
    assert deps.tracer.generations[0][4] is None  # completion
    assert "simulated LLM outage" in deps.tracer.generations[0][5]  # error
