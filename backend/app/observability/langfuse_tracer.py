from contextlib import contextmanager
from app.config import Settings

class _NoopSpan:
    def update(self, **kwargs):
        pass

    def end(self, **kwargs):
        pass

class _NoopTrace:
    def __init__(self):
        self.id = "noop-trace"

    def span(self, **kwargs):
        return _NoopSpan()

    def update(self, **kwargs):
        pass


class LangfuseTracer:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = None
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            from langfuse import Langfuse
            self._client = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def start_trace(self, name: str, investigation_id: str, metadata: dict, input_data: dict | None = None):
        if not self._client:
            return _NoopTrace()
        return self._client.trace(name=name, id=investigation_id, metadata=metadata, input=input_data)

    @contextmanager
    def agent_span(self, trace, agent_name: str, input_data: dict):
        span = trace.span(name=agent_name, input=input_data)
        try:
            yield span
        finally:
            pass

    def llm_generation(
        self, trace, name: str, model: str, system: str, prompt: str,
        completion: str | None, error: str | None = None,
    ) -> None:
        if not self._client:
            return
        try:
            trace.generation(
                name=name,
                model=model,
                input=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                output=completion,
                metadata={"error": error} if error else None,
            )
        except Exception:
            pass

    def flush(self):
        if self._client:
            self._client.flush()

    def trace_url(self, investigation_id: str) -> str | None:
        # Langfuse's real route is /project/{projectId}/traces/{traceId} - a
        # bare /trace/{id} link 404s locally and 500s on Langfuse Cloud, so
        # without a configured project ID there's no valid link to show.
        if not self.enabled or not self._settings.langfuse_project_id:
            return None
        return f"{self._settings.langfuse_public_host}/project/{self._settings.langfuse_project_id}/traces/{investigation_id}"

_tracer_singleton: LangfuseTracer | None = None

def get_tracer(settings: Settings) -> LangfuseTracer:
    global _tracer_singleton
    if _tracer_singleton is None:
        _tracer_singleton = LangfuseTracer(settings)
    return _tracer_singleton
