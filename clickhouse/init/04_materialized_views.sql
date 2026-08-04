-- ============================================================
-- CH-AdNova :: Hourly rollups
--
-- One AggregatingMergeTree target + materialized view per
-- dimension the Investigation Planner / Dimension Explorer
-- agents walk through: overall -> app -> advertiser -> geo ->
-- device/OS -> ad format. Each MV reads only from ad_events (no
-- joins - it's already denormalized), so these are cheap to
-- maintain on insert and cheap to query.
--
-- Metrics stored as SimpleAggregateFunction(sum, ...): summed on
-- merge, and callers still write sum(col) in queries to combine
-- not-yet-merged parts. requests = count(*) (every row is a
-- request; is_filled/is_impression/is_click are funnel flags on
-- top of it).
-- ============================================================

-- ---------- overall ----------
CREATE TABLE IF NOT EXISTS ch_adnova.metrics_hourly_overall
(
    event_hour      DateTime,
    requests        SimpleAggregateFunction(sum, UInt64),
    fills           SimpleAggregateFunction(sum, UInt64),
    impressions     SimpleAggregateFunction(sum, UInt64),
    clicks          SimpleAggregateFunction(sum, UInt64),
    revenue         SimpleAggregateFunction(sum, Float64)
)
ENGINE = AggregatingMergeTree
ORDER BY (event_hour);

CREATE MATERIALIZED VIEW IF NOT EXISTS ch_adnova.mv_metrics_hourly_overall
TO ch_adnova.metrics_hourly_overall
AS
SELECT
    event_hour,
    toUInt64(count())              AS requests,
    toUInt64(sum(is_filled))       AS fills,
    toUInt64(sum(is_impression))   AS impressions,
    toUInt64(sum(is_click))        AS clicks,
    sum(revenue)                   AS revenue
FROM ch_adnova.ad_events
GROUP BY event_hour;

-- ---------- by app ----------
CREATE TABLE IF NOT EXISTS ch_adnova.metrics_hourly_by_app
(
    event_hour      DateTime,
    app_id          LowCardinality(String),
    app_category    LowCardinality(String),
    publisher_tier  LowCardinality(String),
    requests        SimpleAggregateFunction(sum, UInt64),
    fills           SimpleAggregateFunction(sum, UInt64),
    impressions     SimpleAggregateFunction(sum, UInt64),
    clicks          SimpleAggregateFunction(sum, UInt64),
    revenue         SimpleAggregateFunction(sum, Float64)
)
ENGINE = AggregatingMergeTree
ORDER BY (event_hour, app_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS ch_adnova.mv_metrics_hourly_by_app
TO ch_adnova.metrics_hourly_by_app
AS
SELECT
    event_hour,
    app_id,
    any(app_category)               AS app_category,
    any(publisher_tier)              AS publisher_tier,
    toUInt64(count())                AS requests,
    toUInt64(sum(is_filled))         AS fills,
    toUInt64(sum(is_impression))     AS impressions,
    toUInt64(sum(is_click))          AS clicks,
    sum(revenue)                     AS revenue
FROM ch_adnova.ad_events
GROUP BY event_hour, app_id;

-- ---------- by advertiser ----------
CREATE TABLE IF NOT EXISTS ch_adnova.metrics_hourly_by_advertiser
(
    event_hour      DateTime,
    advertiser_id   LowCardinality(String),
    vertical        LowCardinality(String),
    campaign_type   LowCardinality(String),
    requests        SimpleAggregateFunction(sum, UInt64),
    fills           SimpleAggregateFunction(sum, UInt64),
    impressions     SimpleAggregateFunction(sum, UInt64),
    clicks          SimpleAggregateFunction(sum, UInt64),
    revenue         SimpleAggregateFunction(sum, Float64)
)
ENGINE = AggregatingMergeTree
ORDER BY (event_hour, advertiser_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS ch_adnova.mv_metrics_hourly_by_advertiser
TO ch_adnova.metrics_hourly_by_advertiser
AS
SELECT
    event_hour,
    advertiser_id,
    any(vertical)                    AS vertical,
    any(campaign_type)                AS campaign_type,
    toUInt64(count())                 AS requests,
    toUInt64(sum(is_filled))          AS fills,
    toUInt64(sum(is_impression))      AS impressions,
    toUInt64(sum(is_click))           AS clicks,
    sum(revenue)                      AS revenue
FROM ch_adnova.ad_events
GROUP BY event_hour, advertiser_id;

-- ---------- by geo ----------
CREATE TABLE IF NOT EXISTS ch_adnova.metrics_hourly_by_geo
(
    event_hour      DateTime,
    country         LowCardinality(String),
    region          LowCardinality(String),
    requests        SimpleAggregateFunction(sum, UInt64),
    fills           SimpleAggregateFunction(sum, UInt64),
    impressions     SimpleAggregateFunction(sum, UInt64),
    clicks          SimpleAggregateFunction(sum, UInt64),
    revenue         SimpleAggregateFunction(sum, Float64)
)
ENGINE = AggregatingMergeTree
ORDER BY (event_hour, country, region);

CREATE MATERIALIZED VIEW IF NOT EXISTS ch_adnova.mv_metrics_hourly_by_geo
TO ch_adnova.metrics_hourly_by_geo
AS
SELECT
    event_hour,
    country,
    region,
    toUInt64(count())                 AS requests,
    toUInt64(sum(is_filled))          AS fills,
    toUInt64(sum(is_impression))      AS impressions,
    toUInt64(sum(is_click))           AS clicks,
    sum(revenue)                      AS revenue
FROM ch_adnova.ad_events
GROUP BY event_hour, country, region;

-- ---------- by device / OS ----------
CREATE TABLE IF NOT EXISTS ch_adnova.metrics_hourly_by_device
(
    event_hour      DateTime,
    device_model    LowCardinality(String),
    os_version      LowCardinality(String),
    requests        SimpleAggregateFunction(sum, UInt64),
    fills           SimpleAggregateFunction(sum, UInt64),
    impressions     SimpleAggregateFunction(sum, UInt64),
    clicks          SimpleAggregateFunction(sum, UInt64),
    revenue         SimpleAggregateFunction(sum, Float64)
)
ENGINE = AggregatingMergeTree
ORDER BY (event_hour, device_model, os_version);

CREATE MATERIALIZED VIEW IF NOT EXISTS ch_adnova.mv_metrics_hourly_by_device
TO ch_adnova.metrics_hourly_by_device
AS
SELECT
    event_hour,
    device_model,
    os_version,
    toUInt64(count())                 AS requests,
    toUInt64(sum(is_filled))          AS fills,
    toUInt64(sum(is_impression))      AS impressions,
    toUInt64(sum(is_click))           AS clicks,
    sum(revenue)                      AS revenue
FROM ch_adnova.ad_events
GROUP BY event_hour, device_model, os_version;

-- ---------- by ad format ----------
CREATE TABLE IF NOT EXISTS ch_adnova.metrics_hourly_by_format
(
    event_hour      DateTime,
    ad_format       LowCardinality(String),
    requests        SimpleAggregateFunction(sum, UInt64),
    fills           SimpleAggregateFunction(sum, UInt64),
    impressions     SimpleAggregateFunction(sum, UInt64),
    clicks          SimpleAggregateFunction(sum, UInt64),
    revenue         SimpleAggregateFunction(sum, Float64)
)
ENGINE = AggregatingMergeTree
ORDER BY (event_hour, ad_format);

CREATE MATERIALIZED VIEW IF NOT EXISTS ch_adnova.mv_metrics_hourly_by_format
TO ch_adnova.metrics_hourly_by_format
AS
SELECT
    event_hour,
    ad_format,
    toUInt64(count())                 AS requests,
    toUInt64(sum(is_filled))          AS fills,
    toUInt64(sum(is_impression))      AS impressions,
    toUInt64(sum(is_click))           AS clicks,
    sum(revenue)                      AS revenue
FROM ch_adnova.ad_events
GROUP BY event_hour, ad_format;
