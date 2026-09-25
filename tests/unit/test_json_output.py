"""Unit tests for JSON output format across all formatters."""
import json
import pytest
from db_context.schema.formatter import format_as_json


def test_format_as_json_with_dates():
    """Test JSON formatting with date/datetime objects."""
    from datetime import date, datetime
    
    data = {
        "date_field": date(2024, 1, 15),
        "datetime_field": datetime(2024, 1, 15, 10, 30, 0),
        "regular_string": "test"
    }
    
    json_output = format_as_json(data)
    parsed = json.loads(json_output)
    
    assert parsed["date_field"] == "2024-01-15"
    assert parsed["datetime_field"] == "2024-01-15T10:30:00"
    assert parsed["regular_string"] == "test"


def test_format_as_json_with_decimal():
    """Test JSON formatting with Decimal objects."""
    from decimal import Decimal
    
    data = {
        "decimal_value": Decimal("123.45"),
        "integer_value": 42
    }
    
    json_output = format_as_json(data)
    parsed = json.loads(json_output)
    
    # Exact string, never a float
    assert parsed["decimal_value"] == "123.45"
    assert parsed["integer_value"] == 42


def test_format_as_json_with_nested_structures():
    """Test JSON formatting with nested lists and dictionaries."""
    data = {
        "simple_list": [1, 2, 3],
        "nested_dict": {
            "key1": "value1",
            "key2": {
                "nested_key": "nested_value"
            }
        },
        "list_of_dicts": [
            {"id": 1, "name": "first"},
            {"id": 2, "name": "second"}
        ]
    }
    
    json_output = format_as_json(data)
    parsed = json.loads(json_output)
    
    assert parsed["simple_list"] == [1, 2, 3]
    assert parsed["nested_dict"]["key1"] == "value1"
    assert parsed["nested_dict"]["key2"]["nested_key"] == "nested_value"
    assert len(parsed["list_of_dicts"]) == 2
    assert parsed["list_of_dicts"][0]["id"] == 1


def test_format_as_json_with_none_values():
    """Test JSON formatting handles None values correctly."""
    data = {
        "null_field": None,
        "string_field": "value",
        "number_field": 42
    }
    
    json_output = format_as_json(data)
    parsed = json.loads(json_output)
    
    assert parsed["null_field"] is None
    assert parsed["string_field"] == "value"
    assert parsed["number_field"] == 42


def test_format_as_json_decimal_keeps_every_digit():
    """Values beyond double precision survive unchanged."""
    from decimal import Decimal
    value = Decimal("123456789012345678.91")
    parsed = json.loads(format_as_json({"amount": value}))
    assert Decimal(parsed["amount"]) == value


def test_format_as_json_bytes_and_timedelta():
    from datetime import timedelta
    parsed = json.loads(format_as_json({"raw": b"\x00\xff", "span": timedelta(days=1, hours=2)}))
    assert parsed["raw"] == "00ff"
    assert parsed["span"] == "1 day, 2:00:00"


def test_format_as_json_is_compact():
    assert format_as_json({"a": [1, 2]}) == '{"a":[1,2]}'
