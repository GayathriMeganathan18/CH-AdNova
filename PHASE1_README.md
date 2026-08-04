# CH-AdNova — Phase 1: ClickHouse schema + data loading

This phase only touches ClickHouse. It reuses your existing `docker-compose.yml`
as-is — nothing in it needs to change. It slots into the volume mount you
already have:

```yaml
clickhouse:
  volumes:
    - ./clickhouse/init:/docker-entrypoint-initdb.d
```

Drop the `clickhouse/init/*.sql` files from this package into that path and
they'll run automatically, in order, the first time the `clickhouse` container
starts with an empty data volume.

## What's in here

```
clickhouse/
  init/
    01_dimension_tables.sql      apps, advertisers, geo_device (ReplacingMergeTree)
    02_staging_raw_events.sql    ad_events_raw — mirrors the parquet exactly, TTL 7d
    03_fact_table.sql            ad_events — denormalized wide fact table + a projection
    04_materialized_views.sql    6 hourly rollups (overall/app/advertiser/geo/device/format)
    05_dictionary_optional.sql   bonus Dictionary example (not on the critical path)
  load/
    load_data.sh                 loads your 4 files, then denormalizes staging -> fact
    validate.sql                 sanity checks + example investigation-style queries
data/                            put your 4 source files here (see below)
```

## Design notes (why it's built this way)

**Your real schema**, read directly out of the files you gave me:
- `ad_events.parquet`: 9,000,000 rows — `event_time, app_id, geo_device_id,
  advertiser_id, ad_format, is_filled, is_impression, is_click, revenue`
- `apps.txt` (2,000 rows): `app_id, category, publisher_tier`
- `advertisers.txt` (500 rows): `advertiser_id, vertical, campaign_type`
- `geo_device.txt` (5,000 rows): `geo_device_id, region, country, device_model, os_version`

**Denormalize once, at load time, not at query time.** The investigation
agents in Phase 2 will pivot across app/advertiser/country/region/device/OS/
format in an order that depends on what they find — we can't know ahead of
time which dimension combination they'll need. Rather than joining three
dimension tables on every single agent query, `ad_events` is a single wide
table with every dimension attribute already flattened in. Dimension tables
stay as the source of truth for the ETL step and for reference lookups.

**Materialized views, not query-time aggregation.** Every rollup an agent is
likely to ask for first (hourly totals, by app, by advertiser, by geo, by
device/OS, by ad format) is pre-aggregated into an `AggregatingMergeTree`
target table via a `MATERIALIZED VIEW`, so those queries scan rollup rows
instead of the 9M-row fact table. `ad_events` itself remains available for
anything the rollups don't cover (e.g. an unusual dimension combination the
planner decides to check).

**A projection, an optional Dictionary, TTL on staging.** Included to cover
the ClickHouse feature checklist without adding fragility: the projection
re-sorts by `app_id` first for "which app is the root cause" investigations
(the main table is sorted advertiser-first); the Dictionary is a documented
extra, not required by the pipeline; the staging table self-expires after 7
days since nothing should query it directly.

## Running it

```bash
# 1. Put your 4 files here (same ones you uploaded):
mkdir -p data
cp /path/to/apps.txt data/
cp /path/to/advertisers.txt data/
cp /path/to/geo_device.txt data/
cp /path/to/ad_events.parquet data/

# 2. Copy clickhouse/init/*.sql into your existing clickhouse/init/ folder,
#    and clickhouse/load/ alongside it (or just drop this whole `clickhouse/`
#    folder in place — it only adds files, doesn't touch your compose file).

# 3. Start your stack as usual
docker compose up --build -d clickhouse

# 4. Load the data
chmod +x clickhouse/load/load_data.sh
./clickhouse/load/load_data.sh

# 5. Sanity-check it
docker exec -i ch-adnova-clickhouse clickhouse-client --database=ch_adnova \
  --multiquery < clickhouse/load/validate.sql
```

## One thing worth fixing in your `.env`

Your `docker-compose.yml` has mismatched default passwords between services —
the `clickhouse` service defaults `CLICKHOUSE_PASSWORD` to `root`, but the
`backend` service defaults the same variable to `changeme`. Since both read
from the same `${CLICKHOUSE_PASSWORD}` env var, whichever one is actually set
in your `.env` wins for both — just make sure it's set explicitly there so
the backend doesn't try to authenticate with the wrong password. I didn't
touch `docker-compose.yml` itself, per your instructions — just flagging it
so Phase 2 (the backend) doesn't fail on a silent mismatch.

## Verifying it worked

`validate.sql` gives you: row-count parity between staging and the fact
table (any gap means some `app_id`/`advertiser_id`/`geo_device_id` in the
parquet didn't match a dimension row — worth knowing before Phase 2 builds
on top of it), the daily funnel with fill rate / CTR / eCPM, a day-over-day
window-function comparison, top advertisers by revenue, and fill rate by
country.

## Next: Phase 2

FastAPI backend + the 13-agent LangGraph investigation pipeline (Metric
Trigger → Baseline → Anomaly Detection → ... → Narrative → Langfuse Trace),
querying exactly these tables. Say the word when you want to move on to it.
