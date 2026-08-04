#!/usr/bin/env bash
# ============================================================
# CH-AdNova :: data loader
#
# Run this AFTER `docker compose up --build -d` (once the
# clickhouse container is healthy - the init/*.sql files will
# already have created the schema on first boot).
#
# Usage:
#   1. Copy your 4 source files into ./data/ at the repo root:
#        data/apps.txt
#        data/advertisers.txt
#        data/geo_device.txt
#        data/ad_events.parquet
#   2. ./clickhouse/load/load_data.sh
#
# Nothing here modifies your docker-compose.yml or existing
# containers - it only pipes local files into `clickhouse-client`
# running inside the already-running ch-adnova-clickhouse
# container via `docker exec -i`.
# ============================================================
set -euo pipefail

CONTAINER="${CH_CONTAINER:-ch-adnova-clickhouse}"
DB="${CLICKHOUSE_DB:-ch_adnova}"
DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../data" && pwd)"

ch() {
    docker exec -i "$CONTAINER" clickhouse-client --database="$DB" "$@"
}

echo "==> Waiting for $CONTAINER to respond..."
for i in $(seq 1 30); do
    if docker exec "$CONTAINER" wget -q -O- http://localhost:8123/ping >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

echo "==> Loading dimension tables (CSV with header)"
ch --query "INSERT INTO apps FORMAT CSVWithNames" < "$DATA_DIR/apps.txt"
ch --query "INSERT INTO advertisers FORMAT CSVWithNames" < "$DATA_DIR/advertisers.txt"
ch --query "INSERT INTO geo_device FORMAT CSVWithNames" < "$DATA_DIR/geo_device.txt"

echo "==> Dimension row counts:"
ch --query "SELECT 'apps', count() FROM apps"
ch --query "SELECT 'advertisers', count() FROM advertisers"
ch --query "SELECT 'geo_device', count() FROM geo_device"

echo "==> Loading raw event parquet into staging (this is ~9M rows / ~100MB, may take a minute)"
ch --query "INSERT INTO ad_events_raw
    (event_time, app_id, geo_device_id, advertiser_id, ad_format, is_filled, is_impression, is_click, revenue)
    FORMAT Parquet" < "$DATA_DIR/ad_events.parquet"

echo "==> Staging row count:"
ch --query "SELECT count() FROM ad_events_raw"

# advertiser_id is legitimately empty for unfilled requests (is_filled=0) -
# no bid won, so there's no advertiser to attach. An INNER JOIN there drops
# every unfilled row (~22% of the dataset), which silently makes fill_rate
# read as a constant 100% everywhere and makes any fill-rate-driven anomaly
# undetectable. LEFT JOIN keeps those rows; unfilled rows just get an empty
# vertical/campaign_type, which is correct - they never had one.
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

echo "==> Reloading optional dictionary"
ch --query "SYSTEM RELOAD DICTIONARY ch_adnova.dict_advertisers" || true

echo "==> Rollup MV row counts (sanity check):"
ch --query "SELECT 'metrics_hourly_overall', count() FROM metrics_hourly_overall"
ch --query "SELECT 'metrics_hourly_by_app', count() FROM metrics_hourly_by_app"
ch --query "SELECT 'metrics_hourly_by_advertiser', count() FROM metrics_hourly_by_advertiser"
ch --query "SELECT 'metrics_hourly_by_geo', count() FROM metrics_hourly_by_geo"
ch --query "SELECT 'metrics_hourly_by_device', count() FROM metrics_hourly_by_device"
ch --query "SELECT 'metrics_hourly_by_format', count() FROM metrics_hourly_by_format"

echo "==> Done."
