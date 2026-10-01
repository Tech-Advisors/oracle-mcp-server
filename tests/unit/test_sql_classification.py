import pytest
import sqlparse
from db_context.database import DatabaseConnector

@pytest.mark.parametrize("sql,expected", [
    ("SELECT 1 FROM dual", True),
    ("  SELECT * FROM employees", True),
    ("/*comment*/SELECT col FROM t", True),
    ("WITH x AS (SELECT 1 FROM dual) SELECT * FROM x", True),
    ("EXPLAIN SELECT 1 FROM dual", True),
    ("DESCRIBE employees", True),
    ("SHOW something", True),
    ("", False),
    ("   ", False),
    ("SELECT 1; SELECT 2", False),
    ("INSERT INTO t VALUES (1)", False),
    ("UPDATE t SET a=1", False),
    ("DELETE FROM t", False),
    ("CREATE TABLE x(a int)", False),
    ("DROP TABLE x", False),
    ("BEGIN pkg.proc; END;", False),
    # Inline PL/SQL in a WITH clause can write through an autonomous
    # transaction, so it must not pass as a query.
    ("WITH FUNCTION f RETURN NUMBER IS PRAGMA AUTONOMOUS_TRANSACTION; BEGIN "
     "EXECUTE IMMEDIATE 'DELETE FROM t'; COMMIT; RETURN 1; END; SELECT f FROM dual", False),
])
def test_is_select_query(sql, expected):
    assert DatabaseConnector._is_select_query(sql) is expected
