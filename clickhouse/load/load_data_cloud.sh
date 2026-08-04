#!/usr/bin/env bash
# ============================================================
# CH-AdNova :: main dataset loader - ClickHouse Cloud variant
#
# Identical to load_data.sh, but connects to ClickHouse Cloud over
# the network (native protocol, port 9440, TLS) instead of docker
# exec'ing into the local container. Requires clickhouse-client
# installed locally (already present on this machine).
#
# Usage:
#   1. Copy your 4 source files into ./data/ at the repo root (same
#      as load_data.sh):
#        data/apps.txt
#        data/advertisers.txt
#        data/geo_device.txt
#        data/ad_events.parquet
#   2. export CLICKHOUSE_HOST=<your-service>.clickhouse.cloud
#      export CLICKHOUSE_USER=<your-user>
#      export CLICKHOUSE_PASSWORD=<your-password>
#      export CLICKHOUSE_DB=ch_adnova   # optional, defaults below
#   3. ./clickhouse/load/load_data_cloud.sh
#
# Run this AFTER the 01-04 init SQL files have already been applied
# to the Cloud service (skip 05, it's Docker-only).
# ============================================================
set -euo pipefail

: "${CLICKHOUSE_HOST:?Set CLICKHOUSE_HOST to your ClickHouse Cloud hostname first}"
: "${CLICKHOUSE_USER:?Set CLICKHOUSE_USER first}"
: "${CLICKHOUSE_PASSWORD:?Set CLICKHOUSE_PASSWORD first}"
DB="${CLICKHOUSE_DB:-ch_adnova}"
PORT="${CLICKHOUSE_NATIVE_PORT:-9440}"
DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../data" && pwd)"

ch() {
    clickhouse-client --host="$CLICKHOUSE_HOST" --port="$PORT" --secure \
        --user="$CLICKHOUSE_USER" --password="$CLICKHOUSE_PASSWORD" \
        --database="$DB" "$@"
}

echo "==> Loading dimension tables (CSV with header)"
ch --query "INSERT INTO apps FORMAT CSVWithNames" < "$DATA_DIR/apps.txt"
ch --query "INSERT INTO advertisers FORMAT CSVWithNames" < "$DATA_DIR/advertisers.txt"
ch --query "INSERT INTO geo_device FORMAT CSVWithNames" < "$DATA_DIR/geo_device.txt"

echo "==> Dimension row counts:"
ch --query "SELECT 'apps', count() FROM apps"
ch --query "SELECT 'advertisers', count() FROM advertisers"
ch --query "SELECT 'geo_device', count() FROM geo_device"

echo "==> Loading raw event parquet into staging (this is ~9M rows / ~100MB, may take a few minutes over the network)"
ch --query "INSERT INTO ad_events_raw
    (event_time, app_id, geo_device_id, advertiser_id, ad_format, is_filled, is_impression, is_click, revenue)
    FORMAT Parquet" < "$DATA_DIR/ad_events.parquet"

echo "==> Staging row count:"
ch --query "SELECT count() FROM ad_events_raw"

echo "==> Denormalizing staging -> ad_events (single INSERT ... SELECT ... JOIN)"
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

echo "==> Final fact table row count (should match staging - any drop means an ID didn't match a dimension row):"
ch --query "SELECT count() FROM ad_events"

echo "==> Rollup MV row counts (sanity check):"
ch --query "SELECT 'metrics_hourly_overall', count() FROM metrics_hourly_overall"
ch --query "SELECT 'metrics_hourly_by_app', count() FROM metrics_hourly_by_app"
ch --query "SELECT 'metrics_hourly_by_advertiser', count() FROM metrics_hourly_by_advertiser"
ch --query "SELECT 'metrics_hourly_by_geo', count() FROM metrics_hourly_by_geo"
ch --query "SELECT 'metrics_hourly_by_device', count() FROM metrics_hourly_by_device"
ch --query "SELECT 'metrics_hourly_by_format', count() FROM metrics_hourly_by_format"

echo "==> Done."
