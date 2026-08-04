import threading
from datetime import date, timedelta
from typing import Any
import clickhouse_connect
from clickhouse_connect.driver.client import Client
from opentelemetry import trace
from app.config import Settings

_otel_tracer = trace.get_tracer("ch_adnova.clickhouse")

DIMENSION_TABLES: dict[str, dict[str, Any]] = {
    "app": {
        "table": "metrics_hourly_by_app",
        "key": "app_id",
        "meta_cols": ["app_category", "publisher_tier"],
    },
    "advertiser": {
        "table": "metrics_hourly_by_advertiser",
        "key": "advertiser_id",
        "meta_cols": ["vertical", "campaign_type"],
    },
    "geo": {
        "table": "metrics_hourly_by_geo",
        "key": "country",
        "meta_cols": ["region"],
    },
    "device": {
        "table": "metrics_hourly_by_device",
        "key": "device_model",
        "meta_cols": ["os_version"],
    },
    "format": {
        "table": "metrics_hourly_by_format",
        "key": "ad_format",
        "meta_cols": [],
    },
    "os": {
        "table": "metrics_hourly_by_device",
        "key": "os_version",
        "meta_cols": ["device_model"],
    },
    "region": {
        "table": "metrics_hourly_by_geo",
        "key": "region",
        "meta_cols": ["country"],
    },
    "publisher": {
        "table": "metrics_hourly_by_app",
        "key": "publisher_tier",
        "meta_cols": ["app_category"],
    },
}

def _derive(row: dict[str, Any]) -> dict[str, Any]:
    requests = row.get("requests", 0) or 0
    fills = row.get("fills", 0) or 0
    impressions = row.get("impressions", 0) or 0
    clicks = row.get("clicks", 0) or 0
    revenue = row.get("revenue", 0.0) or 0.0
    return {
        **row,
        "fill_rate": (fills / requests) if requests else 0.0,
        "ctr": (clicks / impressions) if impressions else 0.0,
        "ecpm": (revenue / impressions * 1000) if impressions else 0.0,
    }


class ClickHouseRepository:
  
    def __init__(self, settings: Settings):
        self._settings = settings
        self._local = threading.local()

    @property
    def _client(self) -> Client:
        client = getattr(self._local, "client", None)
        if client is None:
            client = clickhouse_connect.get_client(
                host=self._settings.clickhouse_host,
                port=self._settings.clickhouse_http_port,
                username=self._settings.clickhouse_user,
                password=self._settings.clickhouse_password,
                database=self._settings.clickhouse_db,
                secure=self._settings.clickhouse_secure,
            )
            self._local.client = client
        return client

    def _query(self, sql: str, parameters: dict[str, Any] | None = None):
        with _otel_tracer.start_as_current_span("clickhouse.query") as span:
            span.set_attribute("db.system", "clickhouse")
            span.set_attribute("db.statement", sql.strip()[:2000])
            try:
                result = self._client.query(sql, parameters=parameters or {})
                span.set_attribute("db.rows_returned", len(result.result_rows))
                return result
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
                raise

    def ping(self) -> bool:
        return self._client.ping()

    def overall_daily(self, day: date) -> dict[str, Any]:
        sql = """
            SELECT
                sum(requests)    AS requests,
                sum(fills)       AS fills,
                sum(impressions) AS impressions,
                sum(clicks)      AS clicks,
                sum(revenue)     AS revenue
            FROM metrics_hourly_overall
            WHERE toDate(event_hour) = {day:Date}
        """
        result = self._query(sql, parameters={"day": day})
        row = dict(zip(result.column_names, result.result_rows[0])) if result.result_rows else {
            "requests": 0, "fills": 0, "impressions": 0, "clicks": 0, "revenue": 0.0
        }
        return _derive(row), sql.strip()

    def overall_baseline(self, target_date: date, baseline_days: int) -> dict[str, Any]:
        start = target_date - timedelta(days=baseline_days)
        end = target_date - timedelta(days=1)
        sql = """
            SELECT
                sum(requests) / {n:UInt16}    AS requests,
                sum(fills) / {n:UInt16}       AS fills,
                sum(impressions) / {n:UInt16} AS impressions,
                sum(clicks) / {n:UInt16}      AS clicks,
                sum(revenue) / {n:UInt16}     AS revenue
            FROM metrics_hourly_overall
            WHERE toDate(event_hour) BETWEEN {start:Date} AND {end:Date}
        """
        result = self._query(
            sql, parameters={"start": start, "end": end, "n": baseline_days}
        )
        row = dict(zip(result.column_names, result.result_rows[0])) if result.result_rows else {
            "requests": 0, "fills": 0, "impressions": 0, "clicks": 0, "revenue": 0.0
        }
        return _derive(row), sql.strip()

    def daily_series(self, start: date, end: date) -> tuple[list[dict[str, Any]], str]:
        """Day-by-day overall metrics for a range - what the dashboard trend charts render."""
        sql = """
            SELECT
                toDate(event_hour) AS day,
                sum(requests) AS requests, sum(fills) AS fills,
                sum(impressions) AS impressions, sum(clicks) AS clicks,
                sum(revenue) AS revenue
            FROM metrics_hourly_overall
            WHERE toDate(event_hour) BETWEEN {start:Date} AND {end:Date}
            GROUP BY day
            ORDER BY day
        """
        result = self._query(sql, parameters={"start": start, "end": end})
        rows = [_derive(dict(zip(result.column_names, r))) for r in result.result_rows]
        for r in rows:
            r["day"] = str(r["day"])
        return rows, sql.strip()

    def hourly_series(self, start_date: date, end_date: date) -> tuple[list[dict[str, Any]], str]:
        sql = """
            SELECT
                event_hour,
                sum(requests) AS requests, sum(fills) AS fills,
                sum(impressions) AS impressions, sum(clicks) AS clicks,
                sum(revenue) AS revenue
            FROM metrics_hourly_overall
            WHERE toDate(event_hour) BETWEEN {start:Date} AND {end:Date}
            GROUP BY event_hour
            ORDER BY event_hour
        """
        result = self._query(sql, parameters={"start": start_date, "end": end_date})
        rows = [_derive(dict(zip(result.column_names, r))) for r in result.result_rows]
        for r in rows:
            r["hour"] = str(r.pop("event_hour"))
        return rows, sql.strip()

   
    @staticmethod
    def _dimension_where(
        app_id: str | None, region: str | None, publisher_tier: str | None, params: dict[str, Any]
    ) -> str:
        clauses = []
        if app_id:
            clauses.append("app_id = {app_id:String}")
            params["app_id"] = app_id
        if region:
            clauses.append("region = {region:String}")
            params["region"] = region
        if publisher_tier:
            clauses.append("publisher_tier = {publisher_tier:String}")
            params["publisher_tier"] = publisher_tier
        return "".join(f" AND {c}" for c in clauses)

    def filtered_daily_series(
        self, start: date, end: date,
        app_id: str | None = None, region: str | None = None, publisher_tier: str | None = None,
    ) -> tuple[list[dict[str, Any]], str]:
        params: dict[str, Any] = {"start": start, "end": end}
        extra_where = self._dimension_where(app_id, region, publisher_tier, params)
        sql = f"""
            SELECT
                event_date AS day,
                count() AS requests, sum(is_filled) AS fills,
                sum(is_impression) AS impressions, sum(is_click) AS clicks,
                sum(revenue) AS revenue
            FROM ad_events
            WHERE event_date BETWEEN {{start:Date}} AND {{end:Date}}{extra_where}
            GROUP BY day
            ORDER BY day
        """
        result = self._query(sql, parameters=params)
        rows = [_derive(dict(zip(result.column_names, r))) for r in result.result_rows]
        for r in rows:
            r["day"] = str(r["day"])
        return rows, sql.strip()

    def filtered_hourly_series(
        self, start_date: date, end_date: date,
        app_id: str | None = None, region: str | None = None, publisher_tier: str | None = None,
    ) -> tuple[list[dict[str, Any]], str]:
        params: dict[str, Any] = {"start": start_date, "end": end_date}
        extra_where = self._dimension_where(app_id, region, publisher_tier, params)
        sql = f"""
            SELECT
                toStartOfHour(event_time) AS event_hour,
                count() AS requests, sum(is_filled) AS fills,
                sum(is_impression) AS impressions, sum(is_click) AS clicks,
                sum(revenue) AS revenue
            FROM ad_events
            WHERE event_date BETWEEN {{start:Date}} AND {{end:Date}}{extra_where}
            GROUP BY event_hour
            ORDER BY event_hour
        """
        result = self._query(sql, parameters=params)
        rows = [_derive(dict(zip(result.column_names, r))) for r in result.result_rows]
        for r in rows:
            r["hour"] = str(r.pop("event_hour"))
        return rows, sql.strip()

    def filtered_overall_range(
        self, start: date, end: date,
        app_id: str | None = None, region: str | None = None, publisher_tier: str | None = None,
        divide_by: int = 1,
    ) -> tuple[dict[str, Any], str]:
        params: dict[str, Any] = {"start": start, "end": end, "n": divide_by}
        extra_where = self._dimension_where(app_id, region, publisher_tier, params)
        sql = f"""
            SELECT
                count() / {{n:UInt16}} AS requests, sum(is_filled) / {{n:UInt16}} AS fills,
                sum(is_impression) / {{n:UInt16}} AS impressions, sum(is_click) / {{n:UInt16}} AS clicks,
                sum(revenue) / {{n:UInt16}} AS revenue
            FROM ad_events
            WHERE event_date BETWEEN {{start:Date}} AND {{end:Date}}{extra_where}
        """
        result = self._query(sql, parameters=params)
        row = dict(zip(result.column_names, result.result_rows[0])) if result.result_rows else {
            "requests": 0, "fills": 0, "impressions": 0, "clicks": 0, "revenue": 0.0
        }
        return _derive(row), sql.strip()

    def data_date_range(self) -> tuple[date | None, date | None]:
        sql = "SELECT min(toDate(event_hour)), max(toDate(event_hour)) FROM metrics_hourly_overall"
        result = self._query(sql)
        if not result.result_rows:
            return None, None
        row = result.result_rows[0]
        return row[0], row[1]

    def dimension_breakdown(
        self, dimension: str, target_date: date, baseline_days: int
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
        cfg = DIMENSION_TABLES[dimension]
        table = cfg["table"]
        key = cfg["key"]
        meta_select = "".join(f", any({c}) AS {c}" for c in cfg["meta_cols"])
        start = target_date - timedelta(days=baseline_days)
        end = target_date - timedelta(days=1)

        actual_sql = f"""
            SELECT
                {key} {meta_select},
                sum(requests) AS requests, sum(fills) AS fills,
                sum(impressions) AS impressions, sum(clicks) AS clicks,
                sum(revenue) AS revenue
            FROM {table}
            WHERE toDate(event_hour) = {{day:Date}}
            GROUP BY {key}
        """
        baseline_sql = f"""
            SELECT
                {key} {meta_select},
                sum(requests) / {{n:UInt16}} AS requests, sum(fills) / {{n:UInt16}} AS fills,
                sum(impressions) / {{n:UInt16}} AS impressions, sum(clicks) / {{n:UInt16}} AS clicks,
                sum(revenue) / {{n:UInt16}} AS revenue
            FROM {table}
            WHERE toDate(event_hour) BETWEEN {{start:Date}} AND {{end:Date}}
            GROUP BY {key}
        """
        actual_res = self._query(actual_sql, parameters={"day": target_date})
        baseline_res = self._query(
            baseline_sql, parameters={"start": start, "end": end, "n": baseline_days}
        )
        actual_rows = [
            _derive(dict(zip(actual_res.column_names, r))) for r in actual_res.result_rows
        ]
        baseline_rows = [
            _derive(dict(zip(baseline_res.column_names, r))) for r in baseline_res.result_rows
        ]
        return actual_rows, baseline_rows, (actual_sql + "\n--\n" + baseline_sql).strip()

    def filtered_dimension_breakdown(
        self, dimension: str, target_date: date, baseline_days: int,
        filter_column: str, filter_value: str,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
        cfg = DIMENSION_TABLES[dimension]
        key = cfg["key"]
        meta_cols = [c for c in cfg["meta_cols"] if c != filter_column]
        meta_select = "".join(f", any({c}) AS {c}" for c in meta_cols)
        start = target_date - timedelta(days=baseline_days)
        end = target_date - timedelta(days=1)

        actual_sql = f"""
            SELECT
                {key} {meta_select},
                count() AS requests, sum(is_filled) AS fills,
                sum(is_impression) AS impressions, sum(is_click) AS clicks,
                sum(revenue) AS revenue
            FROM ad_events
            WHERE event_date = {{day:Date}} AND {filter_column} = {{filter_value:String}}
            GROUP BY {key}
        """
        baseline_sql = f"""
            SELECT
                {key} {meta_select},
                count() / {{n:UInt16}} AS requests, sum(is_filled) / {{n:UInt16}} AS fills,
                sum(is_impression) / {{n:UInt16}} AS impressions, sum(is_click) / {{n:UInt16}} AS clicks,
                sum(revenue) / {{n:UInt16}} AS revenue
            FROM ad_events
            WHERE event_date BETWEEN {{start:Date}} AND {{end:Date}} AND {filter_column} = {{filter_value:String}}
            GROUP BY {key}
        """
        actual_res = self._query(actual_sql, parameters={"day": target_date, "filter_value": filter_value})
        baseline_res = self._query(
            baseline_sql, parameters={"start": start, "end": end, "n": baseline_days, "filter_value": filter_value}
        )
        actual_rows = [
            _derive(dict(zip(actual_res.column_names, r))) for r in actual_res.result_rows
        ]
        baseline_rows = [
            _derive(dict(zip(baseline_res.column_names, r))) for r in baseline_res.result_rows
        ]
        return actual_rows, baseline_rows, (actual_sql + "\n--\n" + baseline_sql).strip()

    def overall_excluding_segment(
        self, dimension: str, value: str, target_date: date
    ) -> tuple[dict[str, Any], str]:
        cfg = DIMENSION_TABLES[dimension]
        table = cfg["table"]
        key = cfg["key"]
        sql = f"""
            SELECT
                sum(requests) AS requests, sum(fills) AS fills,
                sum(impressions) AS impressions, sum(clicks) AS clicks,
                sum(revenue) AS revenue
            FROM {table}
            WHERE toDate(event_hour) = {{day:Date}} AND {key} != {{value:String}}
        """
        result = self._query(sql, parameters={"day": target_date, "value": value})
        row = dict(zip(result.column_names, result.result_rows[0])) if result.result_rows else {
            "requests": 0, "fills": 0, "impressions": 0, "clicks": 0, "revenue": 0.0
        }
        return _derive(row), sql.strip()

    
    def counterfactual_revenue(
        self,
        dimension: str,
        value: str,
        target_date: date,
        baseline_fill_rate: float,
        baseline_ctr: float,
    ) -> tuple[dict[str, Any], str]:
        cfg = DIMENSION_TABLES[dimension]
        table = cfg["table"]
        key = cfg["key"]
     
        sql = f"""
            SELECT
                sumIf(requests, {key} = {{value:String}})    AS seg_requests,
                sumIf(impressions, {key} = {{value:String}}) AS seg_impressions,
                sumIf(revenue, {key} = {{value:String}})     AS seg_revenue,
                sumIf(revenue, {key} != {{value:String}})    AS rest_revenue
            FROM {table}
            WHERE toDate(event_hour) = {{day:Date}}
        """
        result = self._query(sql, parameters={"day": target_date, "value": value})
        row = dict(zip(result.column_names, result.result_rows[0])) if result.result_rows else {
            "seg_requests": 0, "seg_impressions": 0, "seg_revenue": 0.0, "rest_revenue": 0.0
        }
        seg_requests = row["seg_requests"] or 0
        rest_revenue = row["rest_revenue"] or 0.0
        actual_seg_revenue = row["seg_revenue"] or 0.0
        avg_rev_per_click = 0.0
        if row["seg_impressions"]:
            avg_rev_per_click = (actual_seg_revenue / row["seg_impressions"]) if row["seg_impressions"] else 0.0
        projected_impressions = seg_requests * baseline_fill_rate
        projected_clicks = projected_impressions * baseline_ctr
        projected_seg_revenue = projected_clicks * (avg_rev_per_click / baseline_ctr if baseline_ctr else 0.0) \
            if baseline_ctr else projected_impressions * (actual_seg_revenue / (row["seg_impressions"] or 1))
        projected_total = rest_revenue + projected_seg_revenue
        actual_total = rest_revenue + actual_seg_revenue
        return {
            "actual_total_revenue": actual_total,
            "projected_total_revenue": projected_total,
            "recovered_value": projected_total - actual_total,
        }, sql.strip()


_repo_singleton: ClickHouseRepository | None = None

def get_repository(settings: Settings) -> ClickHouseRepository:
    global _repo_singleton
    if _repo_singleton is None:
        _repo_singleton = ClickHouseRepository(settings)
    return _repo_singleton
