from app.repositories.clickhouse_repo import ClickHouseRepository, _derive

def test_derive_computes_fill_rate_ctr_ecpm():
    row = {"requests": 1000, "fills": 400, "impressions": 380, "clicks": 19, "revenue": 100.0}
    out = _derive(row)
    assert out["fill_rate"] == 0.4
    assert round(out["ctr"], 4) == round(19 / 380, 4)
    assert round(out["ecpm"], 4) == round(100.0 / 380 * 1000, 4)


def test_derive_handles_zero_requests_and_impressions_safely():
    row = {"requests": 0, "fills": 0, "impressions": 0, "clicks": 0, "revenue": 0.0}
    out = _derive(row)
    assert out["fill_rate"] == 0.0
    assert out["ctr"] == 0.0
    assert out["ecpm"] == 0.0


def test_dimension_where_empty_when_no_filters():
    params = {}
    where = ClickHouseRepository._dimension_where(None, None, None, params)
    assert where == ""
    assert params == {}


def test_dimension_where_combines_all_three_filters():
    params = {}
    where = ClickHouseRepository._dimension_where("app_00000", "NAM", "tier_3", params)
    assert " AND app_id = {app_id:String}" in where
    assert " AND region = {region:String}" in where
    assert " AND publisher_tier = {publisher_tier:String}" in where
    assert params == {"app_id": "app_00000", "region": "NAM", "publisher_tier": "tier_3"}


def test_dimension_where_only_includes_provided_filters():
    params = {}
    where = ClickHouseRepository._dimension_where(None, "EU", None, params)
    assert where == " AND region = {region:String}"
    assert params == {"region": "EU"}
