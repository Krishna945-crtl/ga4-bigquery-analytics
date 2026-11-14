-- Daily trend with window functions: 7-day rolling averages, change vs the previous day
-- and week-over-week change. Assumes no missing days (checked in 00_profile_and_quality).
WITH daily AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS day,
    COUNT(DISTINCT user_pseudo_id) AS users,
    ROUND(SUM(IF(event_name = 'purchase', ecommerce.purchase_revenue_in_usd, 0)), 2) AS revenue_usd
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
  GROUP BY day
)
SELECT
  day,
  users,
  revenue_usd,
  ROUND(AVG(users) OVER last_7_days, 1) AS users_7d_avg,
  ROUND(AVG(revenue_usd) OVER last_7_days, 2) AS revenue_7d_avg,
  users - LAG(users) OVER by_day AS users_change_vs_prev_day,
  ROUND(100 * SAFE_DIVIDE(users - LAG(users, 7) OVER by_day, LAG(users, 7) OVER by_day), 1) AS users_wow_pct
FROM daily
WINDOW
  by_day AS (ORDER BY day),
  last_7_days AS (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
ORDER BY day
