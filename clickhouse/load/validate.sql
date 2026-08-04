-- ============================================================
-- CH-AdNova :: sanity + preview queries
-- Run via: docker exec -i ch-adnova-clickhouse clickhouse-client --database=ch_adnova --multiquery < clickhouse/load/validate.sql
-- ============================================================

-- 1. Row counts line up
SELECT 'ad_events_raw' AS tbl, count() AS rows FROM ad_events_raw
UNION ALL
SELECT 'ad_events', count() FROM ad_events;

-- 2. Overall funnel + derived metrics (CTR, fill rate, eCPM) - this is
--    exactly the shape the Metric Trigger / Baseline agents will query.
SELECT
    toDate(event_hour)                         AS day,
    sum(requests)                               AS requests,
    sum(fills)                                  AS fills,
    sum(impressions)                            AS impressions,
    sum(clicks)                                 AS clicks,
    round(sum(fills) / sum(requests), 4)        AS fill_rate,
    round(sum(clicks) / sum(impressions), 4)    AS ctr,
    round(sum(revenue), 2)                      AS revenue,
    round(sum(revenue) / sum(impressions) * 1000, 4) AS ecpm
FROM ch_adnova.metrics_hourly_overall
GROUP BY day
ORDER BY day;

-- 3. Day-over-day revenue with a window function (the kind of moving
--    baseline comparison the Anomaly Detection agent will run)
SELECT
    day,
    revenue,
    lagInFrame(revenue) OVER (ORDER BY day)                     AS prev_day_revenue,
    round(revenue - lagInFrame(revenue) OVER (ORDER BY day), 2) AS delta,
    round(100 * (revenue - lagInFrame(revenue) OVER (ORDER BY day))
          / nullIf(lagInFrame(revenue) OVER (ORDER BY day), 0), 2) AS pct_change
FROM
(
    SELECT toDate(event_hour) AS day, sum(revenue) AS revenue
    FROM ch_adnova.metrics_hourly_overall
    GROUP BY day
)
ORDER BY day;

-- 4. Top advertisers by revenue contribution (dimension drill-down example)
SELECT
    advertiser_id,
    any(vertical)      AS vertical,
    any(campaign_type) AS campaign_type,
    sum(revenue)        AS revenue,
    round(sum(clicks) / nullIf(sum(impressions), 0), 4) AS ctr
FROM ch_adnova.metrics_hourly_by_advertiser
GROUP BY advertiser_id
ORDER BY revenue DESC
LIMIT 10;

-- 5. Fill rate by country (geo dimension example)
SELECT
    country,
    sum(requests) AS requests,
    sum(fills)    AS fills,
    round(sum(fills) / sum(requests), 4) AS fill_rate
FROM ch_adnova.metrics_hourly_by_geo
GROUP BY country
ORDER BY requests DESC;
