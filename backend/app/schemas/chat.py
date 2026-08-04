from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel

Role = Literal["user", "assistant"]

class ChatMessage(BaseModel):
    role: Role
    content: str


class AnomalyBaseline(BaseModel):
    expected: float
    actual: float
    deviation: float
    deviation_pct: float
    severity: str | None = None
    confidence: float | None = None
    model_config = {"extra": "ignore"}


class AnomalyContext(BaseModel):
    id: str
    metric: str
    target_date: date
    severity: str | None = None
    score: float | None = None
    strategy: str | None = None
    threshold: float | None = None
    baseline: AnomalyBaseline | None = None
    detected_at: datetime | None = None
    status: str | None = None
    source: str | None = None
    investigation_id: str | None = None
    root_cause_summary: str | None = None
    executive_summary: str | None = None
    model_config = {"extra": "ignore"}


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    anomaly: AnomalyContext | None = None


class ChatResponse(BaseModel):
    reply: str
    used_llm: bool
    evidence: dict | None = None
