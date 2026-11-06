import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from costing import (  # noqa: E402
    BYTES_PER_TIB,
    MIN_BILLED_BYTES,
    Comparison,
    billed_bytes,
    estimated_cost_usd,
    reduction_pct,
    render_table,
)

QUERIES = Path(__file__).resolve().parents[1] / "sql" / "queries"


def test_one_tib_costs_list_price():
    assert estimated_cost_usd(BYTES_PER_TIB, usd_per_tib=6.25) == pytest.approx(6.25)


def test_minimum_billing_applies_to_tiny_queries():
    assert billed_bytes(1) == MIN_BILLED_BYTES
    assert billed_bytes(0) == 0


def test_negative_bytes_rejected():
    with pytest.raises(ValueError):
        billed_bytes(-1)


@pytest.mark.parametrize("base,opt,expected", [(100, 10, 90.0), (100, 100, 0.0), (0, 5, 0.0)])
def test_reduction_pct(base, opt, expected):
    assert reduction_pct(base, opt) == expected


def test_render_table_has_one_line_per_query():
    rows = [Comparison("a", 2 * 1024**3, 1024**3), Comparison("b", 1024**3, 1024**2)]
    out = render_table(rows).splitlines()
    assert len(out) == 4 and "50.0%" in out[2]


def test_every_query_is_templated_and_filters_by_date():
    files = list(QUERIES.glob("*.sql"))
    assert files
    for f in files:
        sql = f.read_text()
        assert "{table}" in sql
        assert "trip_start_timestamp" in sql.split("WHERE", 1)[1]  # required by require_partition_filter
