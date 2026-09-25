"""The output type handler decides which Python type each column is fetched as."""
from decimal import Decimal
from types import SimpleNamespace

import oracledb

from db_context.database import _exact_output_type_handler


class _FakeCursor:
    arraysize = 100

    def var(self, typ, arraysize):
        return ("var", typ, arraysize)


def _meta(type_code, precision=0, scale=0):
    return SimpleNamespace(type_code=type_code, precision=precision, scale=scale)


def test_declared_integer_keeps_default_int():
    assert _exact_output_type_handler(_FakeCursor(), _meta(oracledb.DB_TYPE_NUMBER, 10, 0)) is None


def test_number_with_scale_is_decimal():
    assert _exact_output_type_handler(_FakeCursor(), _meta(oracledb.DB_TYPE_NUMBER, 12, 2))[1] is Decimal


def test_unspecified_number_is_decimal():
    # SUM(), COUNT() and bare NUMBER columns: precision 0, scale -127
    assert _exact_output_type_handler(_FakeCursor(), _meta(oracledb.DB_TYPE_NUMBER, 0, -127))[1] is Decimal


def test_lobs_are_fetched_as_values():
    cur = _FakeCursor()
    assert _exact_output_type_handler(cur, _meta(oracledb.DB_TYPE_CLOB))[1] is oracledb.DB_TYPE_LONG
    assert _exact_output_type_handler(cur, _meta(oracledb.DB_TYPE_NCLOB))[1] is oracledb.DB_TYPE_LONG
    assert _exact_output_type_handler(cur, _meta(oracledb.DB_TYPE_BLOB))[1] is oracledb.DB_TYPE_LONG_RAW


def test_other_types_untouched():
    assert _exact_output_type_handler(_FakeCursor(), _meta(oracledb.DB_TYPE_VARCHAR)) is None
