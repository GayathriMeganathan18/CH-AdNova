-- ============================================================
-- CH-AdNova :: Dimension tables
-- Small, slowly-changing lookup tables. ReplacingMergeTree so
-- re-running the loader with an updated CSV is idempotent.
-- ============================================================

CREATE TABLE IF NOT EXISTS ch_adnova.apps
(
    app_id          String,
    category        LowCardinality(String),
    publisher_tier  LowCardinality(String)
)
ENGINE = ReplacingMergeTree
ORDER BY app_id;

CREATE TABLE IF NOT EXISTS ch_adnova.advertisers
(
    advertiser_id   String,
    vertical        LowCardinality(String),
    campaign_type   LowCardinality(String)
)
ENGINE = ReplacingMergeTree
ORDER BY advertiser_id;

CREATE TABLE IF NOT EXISTS ch_adnova.geo_device
(
    geo_device_id   String,
    region          LowCardinality(String),
    country         LowCardinality(String),
    device_model    LowCardinality(String),
    os_version      LowCardinality(String)
)
ENGINE = ReplacingMergeTree
ORDER BY geo_device_id;
