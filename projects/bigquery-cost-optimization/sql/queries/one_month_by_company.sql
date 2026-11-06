-- Monthly revenue per company: a typical dashboard query (date range filter).
SELECT company, COUNT(*) AS trips, ROUND(SUM(trip_total), 2) AS revenue
FROM {table}
WHERE trip_start_timestamp >= TIMESTAMP('2023-03-01')
  AND trip_start_timestamp <  TIMESTAMP('2023-04-01')
GROUP BY company
ORDER BY revenue DESC
