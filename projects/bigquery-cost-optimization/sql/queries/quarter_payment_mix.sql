-- Quarterly payment mix (wider date range, few columns).
SELECT payment_type, COUNT(*) AS trips, ROUND(SUM(fare), 2) AS fares
FROM {table}
WHERE trip_start_timestamp >= TIMESTAMP('2023-01-01')
  AND trip_start_timestamp <  TIMESTAMP('2023-04-01')
GROUP BY payment_type
ORDER BY trips DESC
