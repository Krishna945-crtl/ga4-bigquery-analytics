-- E-commerce funnel: how many users reach each step and where they drop off.
-- Open funnel: a user counts at a step if they fired that event at any time in the period.
WITH steps AS (
  SELECT
    COUNT(DISTINCT IF(event_name = 'view_item', user_pseudo_id, NULL)) AS view_item,
    COUNT(DISTINCT IF(event_name = 'add_to_cart', user_pseudo_id, NULL)) AS add_to_cart,
    COUNT(DISTINCT IF(event_name = 'begin_checkout', user_pseudo_id, NULL)) AS begin_checkout,
    COUNT(DISTINCT IF(event_name = 'purchase', user_pseudo_id, NULL)) AS purchase
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
),
funnel AS (
  SELECT 1 AS step_order, 'View item' AS step, view_item AS users FROM steps
  UNION ALL SELECT 2, 'Add to cart', add_to_cart FROM steps
  UNION ALL SELECT 3, 'Begin checkout', begin_checkout FROM steps
  UNION ALL SELECT 4, 'Purchase', purchase FROM steps
)
SELECT
  step_order,
  step,
  users,
  ROUND(100 * SAFE_DIVIDE(users, FIRST_VALUE(users) OVER (ORDER BY step_order)), 1) AS pct_of_first_step,
  ROUND(100 * SAFE_DIVIDE(users, LAG(users) OVER (ORDER BY step_order)), 1) AS pct_of_previous_step
FROM funnel
ORDER BY step_order
