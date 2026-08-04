from datetime import date
from app.schemas.chat import AnomalyBaseline, AnomalyContext, ChatMessage, ChatRequest
from app.services.chat_service import build_investigation_kickoff_text, chat_reply, gather_anomaly_evidence
from conftest import FailingFakeLLM, FakeLLM, FakeRepo, WorkingFakeLLM


def _anomaly(**overrides) -> AnomalyContext:
    base = dict(
        id="a1", metric="fill_rate", target_date=date(2026, 1, 15),
        severity="high", score=-31.2, strategy="pct_deviation", threshold=8.0,
        baseline=AnomalyBaseline(
            expected=0.5, actual=0.34, deviation=-0.16, deviation_pct=-31.2, severity="high", confidence=0.9
        ),
        status="detected", source="manual",
    )
    base.update(overrides)
    return AnomalyContext(**base)


def test_gather_anomaly_evidence_reuses_existing_repo_calls():
    evidence = gather_anomaly_evidence(FakeRepo(), _anomaly(), baseline_days=7)
    assert evidence["target_date"] == "2026-01-15"
    assert set(evidence["comparison"]) == {
        "requests", "fills", "impressions", "clicks", "revenue", "fill_rate", "ctr", "ecpm",
    }
    for v in evidence["comparison"].values():
        assert v["before"] is not None
        assert v["during"] is not None
    assert isinstance(evidence["top_apps"], list)
    assert isinstance(evidence["top_regions"], list)


def test_fallback_reply_without_llm_is_evidence_grounded():
    request = ChatRequest(messages=[ChatMessage(role="user", content="investigate")], anomaly=_anomaly())
    response = chat_reply(FakeRepo(), FakeLLM(), request)
    assert response.used_llm is False
    assert "**Likely Root Cause**" in response.reply
    assert "**Evidence**" in response.reply
    assert response.evidence is not None


def test_fallback_reply_without_anomaly_explains_missing_llm():
    request = ChatRequest(messages=[ChatMessage(role="user", content="hi")], anomaly=None)
    response = chat_reply(FakeRepo(), FakeLLM(), request)
    assert response.used_llm is False
    assert "ANTHROPIC_API_KEY" in response.reply
    assert response.evidence is None


def test_llm_reply_used_when_enabled():
    request = ChatRequest(messages=[ChatMessage(role="user", content="investigate")], anomaly=_anomaly())
    response = chat_reply(FakeRepo(), WorkingFakeLLM(), request)
    assert response.used_llm is True
    assert response.reply
    assert response.evidence is not None


def test_llm_failure_falls_back_without_crashing():
    request = ChatRequest(messages=[ChatMessage(role="user", content="investigate")], anomaly=_anomaly())
    response = chat_reply(FakeRepo(), FailingFakeLLM(), request)
    assert response.used_llm is False
    assert "**Likely Root Cause**" in response.reply


def test_kickoff_text_is_built_from_anomaly_not_hardcoded():
    anomaly = _anomaly(metric="revenue", target_date=date(2026, 2, 1), severity="medium")
    text = build_investigation_kickoff_text(anomaly)
    assert "revenue" in text
    assert "2026-02-01" in text
    assert "medium" in text
