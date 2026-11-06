"""Pure transformation helpers for the Open-Meteo ingestion.

Kept free of any Google Cloud import so they can be unit-tested anywhere.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_VARIABLES = ("temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m")


@dataclass(frozen=True)
class City:
    name: str
    latitude: float
    longitude: float


DEFAULT_CITIES: tuple[City, ...] = (
    City("Santiago", -33.45, -70.66),
    City("Valparaiso", -33.05, -71.62),
    City("Concepcion", -36.83, -73.05),
    City("Antofagasta", -23.65, -70.40),
    City("Puerto Montt", -41.47, -72.94),
)


def build_request_params(city: City, past_days: int = 1) -> dict[str, Any]:
    """Query string parameters for one city."""
    if past_days < 0 or past_days > 92:
        raise ValueError("past_days must be between 0 and 92")
    return {
        "latitude": city.latitude,
        "longitude": city.longitude,
        "hourly": ",".join(HOURLY_VARIABLES),
        "past_days": past_days,
        "forecast_days": 1,
        "timezone": "UTC",
    }


def parse_hourly(payload: dict[str, Any], city: City, ingested_at: datetime) -> list[dict[str, Any]]:
    """Flatten Open-Meteo's column-oriented ``hourly`` block into one row per hour.

    Raises ``ValueError`` when the arrays are missing or have different lengths,
    so a malformed response never lands half-written in the raw zone.
    """
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict) or "time" not in hourly:
        raise ValueError(f"{city.name}: response has no hourly.time block")

    times = hourly["time"]
    columns = {var: hourly.get(var) for var in HOURLY_VARIABLES}
    for var, values in columns.items():
        if values is None or len(values) != len(times):
            raise ValueError(f"{city.name}: hourly.{var} missing or length mismatch")

    ingested = ingested_at.astimezone(timezone.utc).isoformat()
    rows = []
    for i, ts in enumerate(times):
        rows.append(
            {
                "city": city.name,
                "latitude": city.latitude,
                "longitude": city.longitude,
                # Open-Meteo returns "YYYY-MM-DDTHH:MM" in the requested timezone (UTC).
                "observed_at": f"{ts}:00+00:00",
                "temperature_c": columns["temperature_2m"][i],
                "relative_humidity_pct": columns["relative_humidity_2m"][i],
                "precipitation_mm": columns["precipitation"][i],
                "wind_speed_kmh": columns["wind_speed_10m"][i],
                "ingested_at": ingested,
            }
        )
    return rows


def to_ndjson(rows: Iterable[dict[str, Any]]) -> str:
    """Newline-delimited JSON, the format BigQuery load jobs read natively."""
    return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)


def object_path(run_date: str, run_id: str) -> str:
    """Hive-style partitioned path in the raw bucket: raw/weather/dt=YYYY-MM-DD/<run_id>.json."""
    datetime.strptime(run_date, "%Y-%m-%d")  # validates the format
    if not run_id or "/" in run_id:
        raise ValueError("run_id must be a non-empty string without '/'")
    return f"raw/weather/dt={run_date}/{run_id}.json"
