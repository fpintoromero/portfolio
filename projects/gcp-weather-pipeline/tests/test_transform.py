import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ingestion" / "cloud_function"))

from transform import (  # noqa: E402
    DEFAULT_CITIES,
    HOURLY_VARIABLES,
    City,
    build_request_params,
    object_path,
    parse_hourly,
    to_ndjson,
)

SANTIAGO = City("Santiago", -33.45, -70.66)
NOW = datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc)


def sample_payload(n: int = 3) -> dict:
    return {
        "hourly": {
            "time": [f"2026-11-06T{h:02d}:00" for h in range(n)],
            "temperature_2m": [14.1, 13.8, 13.2][:n],
            "relative_humidity_2m": [60, 62, 65][:n],
            "precipitation": [0.0, 0.0, 0.2][:n],
            "wind_speed_10m": [5.4, 4.9, 6.1][:n],
        }
    }


def test_build_request_params_includes_all_variables():
    params = build_request_params(SANTIAGO)
    assert params["hourly"].split(",") == list(HOURLY_VARIABLES)
    assert params["timezone"] == "UTC"
    assert params["latitude"] == -33.45


@pytest.mark.parametrize("bad", [-1, 93])
def test_build_request_params_rejects_out_of_range_days(bad):
    with pytest.raises(ValueError):
        build_request_params(SANTIAGO, past_days=bad)


def test_parse_hourly_flattens_one_row_per_hour():
    rows = parse_hourly(sample_payload(), SANTIAGO, NOW)
    assert len(rows) == 3
    first = rows[0]
    assert first["city"] == "Santiago"
    assert first["observed_at"] == "2026-11-06T00:00:00+00:00"
    assert first["temperature_c"] == 14.1
    assert first["ingested_at"] == "2026-11-06T12:00:00+00:00"


def test_parse_hourly_rejects_length_mismatch():
    payload = sample_payload()
    payload["hourly"]["precipitation"] = [0.0]
    with pytest.raises(ValueError, match="length mismatch"):
        parse_hourly(payload, SANTIAGO, NOW)


def test_parse_hourly_rejects_missing_block():
    with pytest.raises(ValueError, match="no hourly.time"):
        parse_hourly({"error": True}, SANTIAGO, NOW)


def test_to_ndjson_is_one_valid_json_per_line():
    text = to_ndjson(parse_hourly(sample_payload(), SANTIAGO, NOW))
    lines = text.splitlines()
    assert len(lines) == 3
    assert all(json.loads(line)["city"] == "Santiago" for line in lines)
    assert text.endswith("\n")


def test_object_path_is_hive_partitioned():
    assert object_path("2026-11-06", "run1") == "raw/weather/dt=2026-11-06/run1.json"


@pytest.mark.parametrize("run_date,run_id", [("06-11-2026", "r"), ("2026-11-06", ""), ("2026-11-06", "a/b")])
def test_object_path_validates_input(run_date, run_id):
    with pytest.raises(ValueError):
        object_path(run_date, run_id)


def test_default_cities_are_in_chile():
    for city in DEFAULT_CITIES:
        assert -56 < city.latitude < -17 and -76 < city.longitude < -66
