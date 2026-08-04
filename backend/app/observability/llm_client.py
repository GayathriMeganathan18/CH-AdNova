from app.config import Settings

class LLMClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = None
        if settings.anthropic_api_key:
            import anthropic 
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def complete(self, system: str, prompt: str, max_tokens: int = 500) -> str:
        if not self._client:
            raise RuntimeError("LLM client not configured - callers should use their template fallback")
        response = self._client.messages.create(
            model=self._settings.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text").strip()

    def complete_messages(self, system: str, messages: list[dict], max_tokens: int = 700) -> str:
        if not self._client:
            raise RuntimeError("LLM client not configured - callers should use their template fallback")
        response = self._client.messages.create(
            model=self._settings.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return "".join(block.text for block in response.content if block.type == "text").strip()

_llm_singleton: LLMClient | None = None

def get_llm_client(settings: Settings) -> LLMClient:
    global _llm_singleton
    if _llm_singleton is None:
        _llm_singleton = LLMClient(settings)
    return _llm_singleton
