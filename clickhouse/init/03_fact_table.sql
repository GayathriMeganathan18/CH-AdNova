-- ============================================================
-- CH-AdNova :: ad_events (the analytical fact table)
--
-- Fully denormalized on purpose: the investigation agents pivot
-- across app / advertiser / country / region / OS / device /
-- campaign_type / vertical / publisher_tier in arbitrary order
-- and combinations that we can't predict ahead of time. Joining
-- at query time for every agent hop would be slower and harder
-- to reason about than joining once at load time. The dimension
-- tables in 01_dimension_tables.sql remain the source of truth;
-- this table is a query-optimized denormalization of them.
--
-- Partitioned by month (dataset spans a modest date range - no
-- need for daily partitions, which would create excess parts for
-- ~9M rows). Ordered so that the most common investigation
-- entry points (advertiser, then app, then time) are cheap to
-- prune on. A projection re-sorts by app first for the flows
-- that start "which app caused this" instead of "which
-- advertiser".
-- ============================================================

CREATE TABLE IF NOT EXISTS ch_adnova.ad_events
(
    event_time          DateTime64(3),
    event_date          Date MATERIALIZED toDate(event_time),
    event_hour          DateTime MATERIALIZED toStartOfHour(event_time),

    app_id              LowCardinality(String),
    app_category        LowCardinality(String),
    publisher_tier      LowCardinality(String),

    advertiser_id       LowCardinality(String),
    vertical            LowCardinality(String),
    campaign_type       LowCardinality(String),

    geo_device_id       LowCardinality(String),
    region              LowCardinality(String),
    country             LowCardinality(String),
    device_model        LowCardinality(String),
    os_version          LowCardinality(String),

    ad_format           LowCardinality(String),

    is_filled           UInt8,
    is_impression       UInt8,
    is_click            UInt8,
    revenue             Float64,

    PROJECTION proj_by_app
    (
        SELECT *
        ORDER BY (event_date, app_id, advertiser_id, event_time)
    )
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, advertiser_id, app_id, event_time)
SETTINGS index_granularity = 8192;
