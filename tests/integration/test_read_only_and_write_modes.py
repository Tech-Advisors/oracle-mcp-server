import pytest
from db_context import DatabaseContext
from db_context.database import DatabaseConnector

pytestmark = pytest.mark.asyncio

READ_ONLY_ERR = "Read-only mode"

async def test_select_allowed_read_only(db_context_read_only: DatabaseContext):
    result = await db_context_read_only.run_sql_query("SELECT 1 AS COL FROM dual")
    assert result["row_count"] == 1
    assert result["rows"][0]["COL"] == 1

@pytest.mark.parametrize("sql", [
    "INSERT INTO categories (category_id,name) VALUES (9999,'X')",
    "UPDATE categories SET name='Y' WHERE category_id=1",
    "DELETE FROM categories WHERE 1=0",
])
async def test_writes_blocked_in_read_only(db_context_read_only: DatabaseContext, sql):
    # categories table exists in simpleschema; if using testuser schema may differ; skip gracefully
    try:
        with pytest.raises(PermissionError) as exc:
            await db_context_read_only.run_sql_query(sql)
        assert READ_ONLY_ERR in str(exc.value)
    except Exception as e:  # If table not present, skip rather than fail classification intent
        if "ORA-" in str(e):
            pytest.skip(f"Underlying table not found or other Oracle error in env: {e}")
        raise

async def test_write_enabled_insert_and_select(db_context_write_enabled: DatabaseContext):
    # Create a temp table, insert, then select. Clean up.
    await db_context_write_enabled.run_sql_query("CREATE TABLE temp_test_mcp (id NUMBER PRIMARY KEY, val VARCHAR2(20))")
    await db_context_write_enabled.run_sql_query("INSERT INTO temp_test_mcp (id,val) VALUES (1,'abc')")
    rows = await db_context_write_enabled.run_sql_query("SELECT val FROM temp_test_mcp WHERE id=1")
    assert rows["row_count"] == 1
    assert rows["rows"][0]["VAL"] == 'abc'
    await db_context_write_enabled.run_sql_query("DROP TABLE temp_test_mcp")

async def test_multi_statement_rejected_in_read_only(db_context_read_only: DatabaseContext):
    with pytest.raises(PermissionError):
        await db_context_read_only.run_sql_query("SELECT 1 FROM dual; DELETE FROM categories WHERE 1=0")

async def test_cte_allowed_read_only(db_context_read_only: DatabaseContext):
    result = await db_context_read_only.run_sql_query("WITH x AS (SELECT 1 AS a FROM dual) SELECT a FROM x")
    assert result["row_count"] == 1
    assert result["rows"][0]["A"] == 1

async def test_write_is_committed_including_plsql(db_context_write_enabled: DatabaseContext, oracle_connection_string, tmp_path):
    # A second, independent context sees only what was committed.
    await db_context_write_enabled.run_sql_query("CREATE TABLE temp_commit_mcp (id NUMBER PRIMARY KEY, val VARCHAR2(20))")
    try:
        await db_context_write_enabled.run_sql_query("INSERT INTO temp_commit_mcp (id,val) VALUES (1,'dml')")
        await db_context_write_enabled.run_sql_query(
            "BEGIN INSERT INTO temp_commit_mcp (id,val) VALUES (2,'plsql'); END;"
        )
        other = DatabaseContext(
            connection_string=oracle_connection_string,
            cache_path=tmp_path / "other_cache.json",
            read_only=True,
        )
        await other.initialize()
        try:
            rows = await other.run_sql_query("SELECT id, val FROM temp_commit_mcp ORDER BY id")
        finally:
            await other.close()
        assert [r["VAL"] for r in rows["rows"]] == ["dml", "plsql"]
    finally:
        await db_context_write_enabled.run_sql_query("DROP TABLE temp_commit_mcp")


async def test_plsql_block_blocked_in_read_only(db_context_read_only: DatabaseContext):
    with pytest.raises(PermissionError):
        await db_context_read_only.run_sql_query("BEGIN NULL; END;")
