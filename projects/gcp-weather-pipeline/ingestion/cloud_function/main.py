"""HTTP Cloud Function (2nd gen): pull hourly weather from Open-Meteo and land it in GCS.

Flow: Open-Meteo API -> NDJSON file in the raw bucket -> Pub/Sub event with the file path.
Airflow (or any subscriber) picks up the event and loads the file into BigQuery.

Environment variables:
    RAW_BUCKET   name of the raw-zone bucket (required)
    PUBSUB_TOPIC full topic path, projects/<p>/topics/<t> (optional)
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone

import functions_framework
import requests

from transform import DEFAULT_CITIES, OPEN_METEO_URL, build_request_params, object_path, parse_hourly, to_ndjson

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("weather-ingest")


def fetch_city(session: requests.Session, city, past_days: int) -> dict:
    resp = session.get(OPEN_METEO_URL, params=build_request_params(city, past_days), timeout=30)
    resp.raise_for_status()
    return resp.json()


@functions_framework.http
def ingest_weather(request):
    from google.cloud import pubsub_v1, storage  # imported lazily to keep cold start small

    bucket_name = os.environ["RAW_BUCKET"]
    topic = os.environ.get("PUBSUB_TOPIC")
    body = request.get_json(silent=True) or {}
    past_days = int(body.get("past_days", 1))

    now = datetime.now(timezone.utc)
    run_id = body.get("run_id") or f"{now:%Y%m%dT%H%M%S}-{uuid.uuid4().hex[:8]}"
    run_date = body.get("run_date") or now.strftime("%Y-%m-%d")

    rows: list[dict] = []
    with requests.Session() as session:
        for city in DEFAULT_CITIES:
            rows.extend(parse_hourly(fetch_city(session, city, past_days), city, now))

    path = object_path(run_date, run_id)
    storage.Client().bucket(bucket_name).blob(path).upload_from_string(
        to_ndjson(rows), content_type="application/x-ndjson"
    )
    log.info("Wrote %s rows to gs://%s/%s", len(rows), bucket_name, path)

    event = {"bucket": bucket_name, "object": path, "rows": len(rows), "run_id": run_id, "run_date": run_date}
    if topic:
        pubsub_v1.PublisherClient().publish(topic, json.dumps(event).encode("utf-8")).result(timeout=30)

    return event, 200
