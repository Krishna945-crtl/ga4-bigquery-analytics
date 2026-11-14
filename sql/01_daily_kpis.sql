-- Daily KPIs: users, sessions, purchases, revenue and session conversion rate.
-- A session is user_pseudo_id + ga_session_id, the standard way to rebuild GA4 sessions.
WITH events AS (
  SELECT
    PARSE_DATE('%Y%m%d', event_date) AS day,
    user_pseudo_id,
    CONCAT(user_pseudo_id, '-', CAST((SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'ga_session_id') AS STRING)) AS session_id,
    event_name,
    ecommerce.purchase_revenue_in_usd AS revenue_usd
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
)
SELECT
  day,
  COUNT(DISTINCT user_pseudo_id) AS users,
  COUNT(DISTINCT session_id) AS sessions,
  COUNTIF(event_name = 'purchase') AS purchases,
  ROUND(SUM(IF(event_name = 'purchase', revenue_usd, 0)), 2) AS revenue_usd,
  COUNT(DISTINCT IF(event_name = 'purchase', session_id, NULL)) AS purchase_sessions,  -- lets dashboards compute a weighted conversion rate
  ROUND(100 * SAFE_DIVIDE(COUNT(DISTINCT IF(event_name = 'purchase', session_id, NULL)), COUNT(DISTINCT session_id)), 2) AS conversion_pct
FROM events
GROUP BY day
ORDER BY day
