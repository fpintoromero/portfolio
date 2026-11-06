-- Partitioned + clustered copy of a public table for the cost comparison.
-- Replace `portfolio_cost` with your dataset (create it first in the US location).
CREATE SCHEMA IF NOT EXISTS portfolio_cost OPTIONS (location = 'US');

-- Baseline: same rows and columns, no partitioning or clustering (a fair "before").
CREATE OR REPLACE TABLE portfolio_cost.taxi_trips_baseline AS
SELECT
  unique_key, taxi_id, trip_start_timestamp, trip_end_timestamp, trip_seconds, trip_miles,
  pickup_community_area, dropoff_community_area, fare, tips, trip_total, payment_type, company
FROM `bigquery-public-data.chicago_taxi_trips.taxi_trips`
WHERE trip_start_timestamp >= TIMESTAMP('2022-01-01');

-- Optimized: partitioned by day, clustered by the most common filter columns.
CREATE OR REPLACE TABLE portfolio_cost.taxi_trips_optimized
PARTITION BY DATE(trip_start_timestamp)
CLUSTER BY company, payment_type
OPTIONS (
  require_partition_filter = TRUE,          -- every query must prune partitions
  description = 'Partitioned by trip day, clustered by company and payment_type'
) AS
SELECT
  unique_key,
  taxi_id,
  trip_start_timestamp,
  trip_end_timestamp,
  trip_seconds,
  trip_miles,
  pickup_community_area,
  dropoff_community_area,
  fare,
  tips,
  trip_total,
  payment_type,
  company
FROM `bigquery-public-data.chicago_taxi_trips.taxi_trips`
WHERE trip_start_timestamp >= TIMESTAMP('2022-01-01');
