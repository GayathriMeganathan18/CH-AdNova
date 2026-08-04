-- ============================================================
-- CH-AdNova :: Staging table
--
-- Mirrors ad_events.parquet column-for-column. We load the raw
-- parquet in here untouched (no synthetic data, no reshaping),
-- then a single INSERT ... SELECT ... JOIN denormalizes it into
-- the wide analytical fact table (03_fact_table.sql). This keeps
-- "load exactly what was given" and "fast to query" as two
-- separate, auditable steps.
--
-- TTL is short: this table is scratch space, not meant to be
-- queried by the app or the agents.
-- ============================================================

CREATE TABLE IF NOT EXISTS ch_adnova.ad_events_raw
(
    event_time      DateTime64(3),
    app_id          String,
    geo_device_id   String,
    advertiser_id   String,
    ad_format       LowCardinality(String),
    is_filled       UInt8,
    is_impression   UInt8,
    is_click        UInt8,
    revenue         Float64,
    ingested_at     DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (event_time)
TTL ingested_at + INTERVAL 7 DAY;
