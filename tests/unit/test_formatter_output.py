from decimal import Decimal
import json
from db_context.schema.formatter import format_sql_query_result, format_as_json, MAX_CELL_WIDTH


def test_format_sql_query_result_basic_table():
    """Visual/structural snapshot-style test for simple table formatting.

    Ensures:
    - Column padding is applied (NAME column wider than header)
    - Separator uses at least 3 dashes / matches computed widths
    - No truncation note for small values
    - Exact layout is stable (acts as a lightweight snapshot)
    """
    result = {
        "columns": ["ID", "NAME"],
        "rows": [
            {"ID": 1, "NAME": "ALPHA"},
            {"ID": 2, "NAME": "BETA"},
        ],
    }

    table = format_sql_query_result(result)
    expected = "\n".join([
        "| ID | NAME  |",   # NAME padded to width 5
        "| --- | ----- |",  # dashes reflect widths (>=3 rule)
        "| 1  | ALPHA |",   # ID padded to width 2; NAME exact
        "| 2  | BETA  |",   # NAME padded with trailing space
    ])

    assert table == expected, f"Unexpected table formatting:\n{table}"
    assert "Note: Some values truncated" not in table


def test_format_sql_query_result_truncation_and_note():
    """Verify truncation ellipsis and note line appear when cell exceeds MAX_CELL_WIDTH."""
    long_val = "Z" * (MAX_CELL_WIDTH + 25)
    result = {
        "columns": ["COL"],
        "rows": [{"COL": long_val}],
    }
    table = format_sql_query_result(result)

    lines = table.splitlines()
    # Header + separator + data (+ optional note line appended separately if truncation)
    assert lines[0].startswith("| COL")
    assert lines[1].startswith("| ---")
    assert "…" in lines[2], "Truncated ellipsis missing in data row"
    assert any(line.startswith("Note: Some values truncated") for line in lines[3:]), "Truncation note missing"


def test_format_sql_query_result_json_output():
    """Test JSON output format for SQL query results."""
    result = {
        "columns": ["ID", "NAME"],
        "rows": [
            {"ID": 1, "NAME": "ALPHA"},
            {"ID": 2, "NAME": "BETA"},
        ],
        "row_count": 2
    }
    
    json_output = format_sql_query_result(result, output_format="json")
    parsed = json.loads(json_output)
    
    assert parsed["row_count"] == 2
    assert parsed["columns"] == ["ID", "NAME"]
    assert len(parsed["rows"]) == 2
    assert parsed["rows"][0]["ID"] == 1
    assert parsed["rows"][0]["NAME"] == "ALPHA"
    assert parsed["rows"][1]["ID"] == 2
    assert parsed["rows"][1]["NAME"] == "BETA"


def test_format_sql_query_result_json_empty():
    """Test JSON output format for empty query results."""
    result = {
        "columns": ["ID"],
        "rows": [],
        "row_count": 0
    }
    
    json_output = format_sql_query_result(result, output_format="json")
    parsed = json.loads(json_output)
    
    assert parsed["row_count"] == 0
    assert parsed["columns"] == ["ID"]
    assert parsed["rows"] == []
    assert parsed["more_rows_available"] is False


def test_format_as_json_helper():
    """Test the format_as_json helper function."""
    data = {
        "test": "value",
        "number": 42,
        "list": [1, 2, 3],
        "nested": {"key": "value"}
    }
    
    json_output = format_as_json(data)
    parsed = json.loads(json_output)
    
    assert parsed == data


def test_format_sql_query_result_json_flags_capped_result():
    """A result cut short by max_rows must say so."""
    result = {"columns": ["ID"], "rows": [{"ID": 1}], "row_count": 1, "more_rows_available": True}
    parsed = json.loads(format_sql_query_result(result, output_format="json"))
    assert parsed["more_rows_available"] is True


def test_format_sql_query_result_json_keeps_long_values_and_nulls():
    """JSON output neither truncates cells nor conflates NULL with empty text."""
    long_text = "x" * 5000
    result = {
        "columns": ["NOTE", "EMPTY", "MISSING"],
        "rows": [{"NOTE": long_text, "EMPTY": "", "MISSING": None}],
        "row_count": 1,
    }
    parsed = json.loads(format_sql_query_result(result, output_format="json"))
    row = parsed["rows"][0]
    assert row["NOTE"] == long_text
    assert row["EMPTY"] == ""
    assert row["MISSING"] is None


def test_format_sql_query_result_markdown_null_cell():
    """A NULL cell must not crash the markdown table."""
    result = {"columns": ["A", "B"], "rows": [{"A": None, "B": 1}], "row_count": 1}
    out = format_sql_query_result(result)
    assert "| A" in out


def test_format_sql_query_result_json_carries_column_types():
    result = {
        "columns": ["BETRAG"],
        "column_types": {"BETRAG": "NUMBER"},
        "rows": [{"BETRAG": Decimal("1.10")}],
        "row_count": 1,
    }
    parsed = json.loads(format_sql_query_result(result, output_format="json"))
    assert parsed["column_types"] == {"BETRAG": "NUMBER"}
    assert parsed["rows"][0]["BETRAG"] == "1.10"
