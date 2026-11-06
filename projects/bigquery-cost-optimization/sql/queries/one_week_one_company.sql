-- Drill-down: one company, one week (date range + clustered column filter).
SELECT DATE(trip_start_timestamp) AS day, payment_type, COUNT(*) AS trips, ROUND(AVG(tips), 2) AS avg_tip
FROM {table}
WHERE trip_start_timestamp >= TIMESTAMP('2023-03-06')
  AND trip_start_timestamp <  TIMESTAMP('2023-03-13')
  AND company = 'Flash Cab'
GROUP BY day, payment_type
ORDER BY day, payment_type
