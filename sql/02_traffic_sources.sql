-- Which channels bring users who actually buy?
-- traffic_source in the GA4 export is the source that FIRST acquired the user (first touch),
-- so this answers "users first acquired by X", not "sessions from X".
WITH events AS (
  SELECT
    traffic_source.source AS source,
    traffic_source.medium AS medium,
    user_pseudo_id,
    event_name,
    ecommerce.purchase_revenue_in_usd AS revenue_usd
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
)
SELECT
  source,
  medium,
  COUNT(DISTINCT user_pseudo_id) AS users,
  COUNT(DISTINCT IF(event_name = 'purchase', user_pseudo_id, NULL)) AS buyers,
  ROUND(SUM(IF(event_name = 'purchase', revenue_usd, 0)), 2) AS revenue_usd,
  ROUND(100 * SAFE_DIVIDE(COUNT(DISTINCT IF(event_name = 'purchase', user_pseudo_id, NULL)), COUNT(DISTINCT user_pseudo_id)), 2) AS buyer_rate_pct
FROM events
GROUP BY source, medium
ORDER BY users DESC
