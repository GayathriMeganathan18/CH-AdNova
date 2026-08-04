# CH-AdNova — Phase 2: FastAPI backend + LangGraph investigation engine

Builds on Phase 1 (ClickHouse schema + data) — see `PHASE1_README.md` and
`RUNBOOK.md` at the project root first if you haven't run those yet.

## What's in here

```
backend/
├── Dockerfile
├── requirements.txt
├── pytest.ini
├── app/
│   ├── main.py                     FastAPI app + OTel instrumentation
│   ├── config.py                   Settings (env-driven, see table below)
│   ├── dependencies.py              DI wiring for all singletons
│   ├── routers/
│   │   ├── health.py                GET /health
│   │   └── investigate.py           POST /api/investigate, GET /api/investigations[/{id}]
│   ├── schemas/investigation.py     Pydantic request/response contracts
│   ├── repositories/
│   │   ├── clickhouse_repo.py       every SQL query the agents use
│   │   └── investigation_store.py   MongoDB-backed trace persistence
│   ├── services/investigation_service.py   builds state, runs the graph, persists result
│   ├── agents/                      the 12 LangGraph agents + graph.py wiring + state.py
│   ├── observability/
│   │   ├── langfuse_tracer.py       one trace per investigation, one span per agent
│   │   ├── otel_setup.py            OTel export to ClickStack
│   │   └── llm_client.py            narrative-only LLM wrapper, safe no-key fallback
│   └── docs/langgraph_flow.md       mermaid diagram + design notes
└── tests/
    ├── conftest.py                  deterministic FakeRepo (a synthetic device fill-rate drop)
    ├── test_agents_smoke.py         runs all 12 agents end-to-end, asserts correct root cause
    └── test_clickhouse_repo.py      tests the fill_rate/CTR/eCPM derivation math
```

## Design decisions worth knowing

**The LLM never computes a number.** Every field in `InvestigationResult` -
revenue, fill rate, CTR, eCPM, deltas, percentages, confidence, business
impact - is either a direct ClickHouse query result or simple Python
arithmetic on query results (`root_cause_ranking.py`'s confidence blend,
`_derive()`'s fill_rate/ctr/ecpm). The LLM (Claude, via `llm_client.py`) is
only ever asked to phrase already-computed numbers into a sentence -
`hypothesis_generator.py` and `executive_summary.py` - and both have a
template fallback that runs identically well with zero API key configured,
because a hackathon demo (or a judge's laptop) shouldn't be able to fail
just because a key wasn't set.

**The investigation is genuinely dynamic, not a fixed scan.**
`InvestigationPlannerAgent` decides dimension check *order* from which
funnel stage broke, and its `route()` function (the LangGraph conditional
edge) decides whether to keep exploring or stop, based on how concentrated
the findings have been so far. See `docs/langgraph_flow.md` for the exact
logic and a diagram.

**Ruling things out is a first-class output, not an afterthought.**
Every dimension `DimensionExplorerAgent` checks that *doesn't* clear the
concentration threshold gets appended to `state["ruled_out"]` with the
actual number that cleared it (not just "geo: normal"). Same for
hypotheses that don't survive `EvidenceValidationAgent`'s counterfactual
removal check.

**Verified without live infrastructure.** I don't have Docker/network
access in the environment I built this in, so I couldn't run this against
a live ClickHouse/Mongo/Langfuse stack. What I *did* verify: every file
passes `python -m py_compile`, and I ran the full 12-agent chain against a
hand-built deterministic fake repository (a synthetic fill-rate drop
concentrated in one device) end-to-end in a plain Python script - it
correctly isolated the broken funnel stage, prioritized the right
dimension, flagged the right segment, ranked it with a computed
confidence, ran the counterfactual, and produced coherent recommendations
and a summary. That's real logic verification, but it is not the same as
running `pytest` with the actual `fastapi`/`langgraph`/`clickhouse-connect`
packages installed - do that as your first step (see Testing below) before
trusting this in front of judges.

## Environment variables (backend-specific)

These are already declared in your `docker-compose.yml`'s `backend`
service `environment:` block - nothing new to add there. Add the two LLM
ones to your root `.env` if you want narrative text from Claude instead of
the template fallback (everything works without them):

| Variable | Required? | Notes |
|---|---|---|
| `CLICKHOUSE_HOST`, `CLICKHOUSE_DB`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD` | Yes | Already in compose; must match what Phase 1 loaded |
| `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` | No | Without keys, tracing becomes a documented no-op |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Yes (defaulted) | Points at ClickStack; already in compose |
| `ANTHROPIC_API_KEY` *(new — add to `.env`)* | No | Enables LLM narrative text; template fallback used otherwise |
| `ANTHROPIC_MODEL` *(new — add to `.env`, defaults to `claude-sonnet-4-6`)* | No | Which Claude model to call for narrative text |

## API

### `POST /api/investigate`
```bash
curl -X POST http://localhost:8000/api/investigate \
  -H "Content-Type: application/json" \
  -d '{"metric": "revenue", "target_date": "2026-01-15", "baseline_days": 7}'
```
Returns a full `InvestigationResult`: trigger, funnel checks, every
dimension explored (with SQL), ruled-out list, ranked root causes with
confidence and business impact, counterfactual, recommendations, executive
summary, full agent log, and a Langfuse trace URL (if configured).

### `GET /api/investigations/{investigation_id}`
Fetch a previously run investigation from MongoDB.

### `GET /api/investigations`
List the 20 most recent investigations (summary fields only).

### `GET /health`
```json
{"status": "ok", "clickhouse": "up"}
```

## Testing guide

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

Expected: 8 tests pass. `test_agents_smoke.py` is the important one - it
proves the planner correctly orders dimensions after a fill-rate break,
the explorer correctly flags the perturbed device segment and rules out
the flat one, and the full chain lands on the right root cause with a
populated counterfactual. `test_clickhouse_repo.py` locks down the
fill_rate/CTR/eCPM arithmetic independent of any live database.

To test against a **real** ClickHouse (once Phase 1's `load_data.sh` has
run), skip the fakes and hit the live endpoint:
```bash
docker compose up --build -d clickhouse postgres mongodb langfuse clickstack backend
curl -X POST http://localhost:8000/api/investigate \
  -H "Content-Type: application/json" \
  -d '{"metric": "revenue", "target_date": "<a date present in your data>", "baseline_days": 7}'
```
Pick `target_date` from a day your `ad_events` table actually covers -
check with:
```sql
SELECT min(toDate(event_time)), max(toDate(event_time)) FROM ch_adnova.ad_events;
```

## Demo guide

1. `docker compose up --build -d clickhouse postgres mongodb langfuse clickstack backend`
2. `./clickhouse/load/load_data.sh` (if you haven't already)
3. Pick a real date range from the query above
4. `curl -X POST http://localhost:8000/api/investigate ...` with that date
5. Read the response top-down: `trigger` (was it actually anomalous?) →
   `funnel_checks` (which stage broke?) → `explorations` (what was checked,
   in what order, what got ruled out) → `root_causes` (ranked, with
   confidence + business impact) → `counterfactual` → `recommendations` →
   `executive_summary`
6. If Langfuse keys are set, open `http://localhost:3001` and find the
   trace by the `investigation_id` in the response - one span per agent

## Next: Phase 3

React/Vite/Tailwind/ECharts frontend consuming this API, plus the
`mcp-server` service. Say the word when you want to move on.
