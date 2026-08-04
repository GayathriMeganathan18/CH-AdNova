"""
CH-AdNova MCP server.

Exposes a single tool, `query_clickhouse`, so any MCP-compatible client
(Claude Desktop, an IDE, another agent) can explore the same ClickHouse
schema the investigation backend uses - read-only, SELECT-only, capped
result size. This is deliberately NOT how the LangGraph backend talks to
ClickHouse (that goes through app/repositories/clickhouse_repo.py directly,
for typed, purpose-built queries) - this server is for ad-hoc human/agent
exploration of the same data outside the fixed investigation flow.
"""
import os
import re

import clickhouse_connect
from mcp.server.fastmcp import FastMCP

CLICKHOUSE_HOST = os.environ.get("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_HTTP_PORT = 8123  # container-internal port - see backend/app/config.py for why
CLICKHOUSE_DB = os.environ.get("CLICKHOUSE_DB", "ch_adnova")
CLICKHOUSE_USER = os.environ.get("CLICKHOUSE_USER", "ch_adnova_admin")
CLICKHOUSE_PASSWORD = os.environ.get("CLICKHOUSE_PASSWORD", "root")

MAX_ROWS = 500
FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|rename|grant|revoke|attach|detach|optimize|kill|system)\b",
    re.IGNORECASE,
)

mcp = FastMCP(
    "ch-adnova-clickhouse",
    host="0.0.0.0",
    port=int(os.environ.get("MCP_SERVER_PORT", "8001")),
)


def _client():
    return clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_HTTP_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
    )


@mcp.tool()
def list_tables() -> list[str]:
    """List every table and materialized view available in the ch_adnova database."""
    result = _client().query("SHOW TABLES")
    return [row[0] for row in result.result_rows]


@mcp.tool()
def describe_table(table_name: str) -> list[dict]:
    """Show the column names and types for a given table (e.g. 'ad_events', 'metrics_hourly_by_app')."""
    if not re.fullmatch(r"[A-Za-z0-9_]+", table_name):
        raise ValueError("Invalid table name")
    result = _client().query(f"DESCRIBE TABLE {table_name}")
    return [dict(zip(result.column_names, row)) for row in result.result_rows]


@mcp.tool()
def query_clickhouse(sql: str) -> dict:
    """
    Run a read-only SELECT query against the ch_adnova ClickHouse database
    and return up to 500 rows. INSERT/UPDATE/DELETE/DDL statements are
    rejected. Use list_tables()/describe_table() first to see the schema.
    """
    stripped = sql.strip().rstrip(";")
    if not re.match(r"^\s*(SELECT|WITH)\b", stripped, re.IGNORECASE):
        raise ValueError("Only SELECT/WITH (read-only) queries are allowed")
    if FORBIDDEN.search(stripped):
        raise ValueError("Query contains a disallowed keyword for this read-only tool")

    limited_sql = f"SELECT * FROM ({stripped}) LIMIT {MAX_ROWS}"
    result = _client().query(limited_sql)
    return {
        "columns": result.column_names,
        "rows": [list(row) for row in result.result_rows],
        "row_count": len(result.result_rows),
        "truncated_to": MAX_ROWS,
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
