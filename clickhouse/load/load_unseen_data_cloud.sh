#!/usr/bin/env bash
# ============================================================
# CH-AdNova :: unseen-incident dataset loader - ClickHouse Cloud variant
#
# Identical to load_unseen_data.sh, but connects to ClickHouse Cloud
# over the network (native protocol, port 9440, TLS) instead of
# docker exec'ing into the local container. Run load_data_cloud.sh
# first - this appends the Jul 6-10 incident data on top of it.
#
# Usage:
#   1. The 4 files should already be in ./data/unseen_data/:
#        apps.csv, advertisers.csv, geo_device.csv, ad_events.parquet
#   2. export CLICKHOUSE_HOST=<your-service>.clickhouse.cloud
#      export CLICKHOUSE_USER=<your-user>
#      export CLICKHOUSE_PASSWORD=<your-password>
#      export CLICKHOUSE_DB=ch_adnova   # optional, defaults below
#   3. ./clickhouse/load/load_unseen_data_cloud.sh
# ============================================================
set -euo pipefail

: "${CLICKHOUSE_HOST:?Set CLICKHOUSE_HOST to your ClickHouse Cloud hostname first}"
: "${CLICKHOUSE_USER:?Set CLICKHOUSE_USER first}"
: "${CLICKHOUSE_PASSWORD:?Set CLICKHOUSE_PASSWORD first}"
DB="${CLICKHOUSE_DB:-ch_adnova}"
PORT="${CLICKHOUSE_NATIVE_PORT:-9440}"
DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../data/unseen_data" && pwd)"

ch() {
    clickhouse-client --host="$CLICKHOUSE_HOST" --port="$PORT" --secure \
        --user="$CLICKHOUSE_USER" --password="$CLICKHOUSE_PASSWORD" \
        --database="$DB" "$@"
}

echo "==> ad_events row count before this load:"
ch --query "SELECT count() FROM ad_events"

echo "==> Truncating dimension tables (IDs are reused with regenerated attributes - must replace, not append)"
ch --query "TRUNCATE TABLE apps"
ch --query "TRUNCATE TABLE advertisers"
ch --query "TRUNCATE TABLE geo_device"

echo "==> Loading regenerated dimension tables"
ch --query "INSERT INTO apps FORMAT CSVWithNames" < "$DATA_DIR/apps.csv"
ch --query "INSERT INTO advertisers FORMAT CSVWithNames" < "$DATA_DIR/advertisers.csv"
ch --query "INSERT INTO geo_device FORMAT CSVWithNames" < "$DATA_DIR/geo_device.csv"

echo "==> Dimension row counts (expect 2000 / 500 / 5000):"
ch --query "SELECT 'apps', count() FROM apps"
ch --query "SELECT 'advertisers', count() FROM advertisers"
ch --query "SELECT 'geo_device', count() FROM geo_device"

echo "==> Truncating staging (may still hold the main dataset's rows under its 7-day TTL - must not reprocess those)"
ch --query "TRUNCATE TABLE ad_events_raw"

echo "==> Loading unseen-incident event parquet into staging"
ch --query "INSERT INTO ad_events_raw
    (event_time, app_id, geo_device_id, advertiser_id, ad_format, is_filled, is_impression, is_click, revenue)
    FORMAT Parquet" < "$DATA_DIR/ad_events.parquet"

echo "==> Staging row count (expect ~1.5M, NOT ~9M+1.5M):"
ch --query "SELECT count() FROM ad_events_raw"

echo "==> Denormalizing staging -> ad_events (appends alongside existing history, does not replace it)"
ch --query "
INSERT INTO ad_events
(
    event_time, app_id, app_category, publisher_tier,
    advertiser_id, vertical, campaign_type,
    geo_device_id, region, country, device_model, os_version,
    ad_format, is_filled, is_impression, is_click, revenue
)
SELECT
    e.event_time,
    e.app_id,        a.category,      a.publisher_tier,
    e.advertiser_id, adv.vertical,    adv.campaign_type,
    e.geo_device_id, g.region,        g.country, g.device_model, g.os_version,
    e.ad_format, e.is_filled, e.is_impression, e.is_click, e.revenue
FROM ad_events_raw e
INNER JOIN apps a         ON e.app_id = a.app_id
LEFT JOIN advertisers adv ON e.advertiser_id = adv.advertiser_id
INNER JOIN geo_device g    ON e.geo_device_id = g.geo_device_id
"

echo "==> Final fact table row count and date range (expect old_count + ~1.5M, spanning Jun 1 - Jul 10):"
ch --query "SELECT count(), min(event_date), max(event_date) FROM ad_events"

echo "==> Rollup MV row counts (sanity check - should have grown vs before this run):"
ch --query "SELECT 'metrics_hourly_overall', count() FROM metrics_hourly_overall"
ch --query "SELECT 'metrics_hourly_by_app', count() FROM metrics_hourly_by_app"
ch --query "SELECT 'metrics_hourly_by_advertiser', count() FROM metrics_hourly_by_advertiser"
ch --query "SELECT 'metrics_hourly_by_geo', count() FROM metrics_hourly_by_geo"
ch --query "SELECT 'metrics_hourly_by_device', count() FROM metrics_hourly_by_device"
ch --query "SELECT 'metrics_hourly_by_format', count() FROM metrics_hourly_by_format"

echo "==> Done. The new data covers Jul 6 - Jul 10, 2026 - point an investigation at a date in that range."
