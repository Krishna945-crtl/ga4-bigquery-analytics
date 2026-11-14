-- Profile of the raw GA4 export in one row: totals for the README plus counts that
-- ga4/checks.py turns into PASS / WARN / FAIL data quality rules.
WITH raw AS (
  SELECT
    event_date,
    event_timestamp,
    event_name,
    user_pseudo_id,
    (SELECT ep.value.int_value FROM UNNEST(event_params) AS ep WHERE ep.key = 'ga_session_id') AS ga_session_id,
    ecommerce.purchase_revenue_in_usd AS revenue_usd,
    ecommerce.transaction_id AS transaction_id
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),
sessions AS (
  SELECT *, CONCAT(user_pseudo_id, '-', CAST(ga_session_id AS STRING)) AS session_id
  FROM raw
)
SELECT
  COUNT(*) AS total_events,
  COUNT(DISTINCT user_pseudo_id) AS total_users,
  COUNT(DISTINCT session_id) AS total_sessions,
  COUNT(DISTINCT IF(event_name = 'purchase', session_id, NULL)) AS sessions_with_purchase,
  COUNT(DISTINCT event_date) AS days_with_data,
  DATE_DIFF(DATE '2021-01-31', DATE '2020-11-01', DAY) + 1 AS days_expected,
  COUNTIF(user_pseudo_id IS NULL) AS events_missing_user,
  COUNTIF(ga_session_id IS NULL) AS events_missing_session,
  COUNT(*) - COUNT(DISTINCT CONCAT(COALESCE(user_pseudo_id, ''), '|', CAST(event_timestamp AS STRING), '|', event_name)) AS duplicate_events,
  COUNTIF(event_name = 'purchase') AS purchase_events,
  COUNTIF(event_name = 'purchase' AND (revenue_usd IS NULL OR revenue_usd <= 0)) AS purchases_without_revenue,
  COUNTIF(event_name = 'purchase' AND (transaction_id IS NULL OR transaction_id = '(not set)')) AS purchases_without_transaction_id
FROM sessions
