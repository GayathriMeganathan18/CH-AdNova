#!/usr/bin/env bash
# ============================================================
# CH-AdNova :: unseen-incident dataset loader
#
# Loads InMobi's Click-a-thon 2026 "unseen incident" dataset:
# https://github.com/sidagarwal04/click-a-thon-2026/tree/main/InMobi/unseen_data
# - a continuation of the main dataset (Jul 6-10, 2026, right after
# the main dataset's Jun 1-Jul 5) with new planted anomalies.
#
# IMPORTANT, per that dataset's own spec.md: the three dimension
# CSVs reuse the SAME app_id/advertiser_id/geo_device_id values as
# the main dataset, but their attribute columns (category, tier,
# vertical, region, device, ...) have been REGENERATED. Naively
# re-running load_data.sh against this folder would be wrong twice
# over:
#   1. apps/advertisers/geo_device are ReplacingMergeTree - inserting
#      new rows under the same keys relies on an async background
#      merge to dedup, so old and new attribute values could both be
#      visible (nondeterministically) until that merge happens.
#   2. ad_events_raw (staging) has a 7-day TTL and, on a fresh-enough
#      environment, may still hold the original ~9M rows - re-running
#      the denormalization JOIN would reprocess those into ad_events
#      a second time, duplicating all of history.
#
# This script truncates the three dimension tables and the staging
# table first, so only the unseen dataset's own rows exist when the
# denormalization step runs. It does NOT touch the already-denormalized
# historical rows in ad_events (Jun 1-Jul 5) - those correctly keep the
# dimension attribute values that were true for that period; only the
# new Jul 6-10 rows get the regenerated attributes, and they're
# APPENDED to ad_events, not replacing it.
#
# Usage:
#   1. The 4 files should already be in ./data/unseen_data/:
#        apps.csv, advertisers.csv, geo_device.csv, ad_events.parquet
#   2. ./clickhouse/load/load_unseen_data.sh
# ============================================================
set -euo pipefail

CONTAINER="${CH_CONTAINER:-ch-adnova-clickhouse}"
DB="${CLICKHOUSE_DB:-ch_adnova}"
DATA_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../data/unseen_data" && pwd)"

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

# Same LEFT JOIN reasoning as load_data.sh: advertiser_id is legitimately
# empty for unfilled requests, so INNER JOIN there would silently drop them.
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

echo "==> Reloading optional dictionary"
ch --query "SYSTEM RELOAD DICTIONARY ch_adnova.dict_advertisers" || true

echo "==> Done. The new data covers Jul 6 - Jul 10, 2026 - point an investigation at a date in that range."
