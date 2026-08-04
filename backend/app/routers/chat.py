from fastapi import APIRouter, Depends
from app.config import Settings, get_settings
from app.dependencies import get_llm, get_repo
from app.observability.llm_client import LLMClient
from app.repositories.clickhouse_repo import ClickHouseRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_reply

router = APIRouter(prefix="/api")

@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    repo: ClickHouseRepository = Depends(get_repo),
    llm: LLMClient = Depends(get_llm),
    settings: Settings = Depends(get_settings),
):
    return chat_reply(repo, llm, request, baseline_days=settings.default_baseline_days)
