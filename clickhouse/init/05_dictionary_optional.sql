-- ============================================================
-- CH-AdNova :: Optional Dictionary
--
-- Not on the critical path (ad_events is already denormalized -
-- see 03_fact_table.sql), but included as an example of the
-- Dictionary lookup pattern for any ad-hoc query/agent step that
-- wants to resolve an advertiser_id -> vertical without a join,
-- e.g. dictGet('ch_adnova.dict_advertisers', 'vertical', advertiser_id).
--
-- Uses the same credentials the "clickhouse" service is already
-- started with in docker-compose.yml. If you change
-- CLICKHOUSE_USER/CLICKHOUSE_PASSWORD in your .env, update the
-- two lines below to match.
-- ============================================================

CREATE DICTIONARY IF NOT EXISTS ch_adnova.dict_advertisers
(
    advertiser_id   String,
    vertical        String,
    campaign_type   String
)
PRIMARY KEY advertiser_id
SOURCE(CLICKHOUSE(
    HOST 'localhost'
    PORT 9000
    USER 'ch_adnova_admin'
    PASSWORD 'root'
    DB 'ch_adnova'
    TABLE 'advertisers'
))
LIFETIME(MIN 300 MAX 600)
LAYOUT(HASHED());
