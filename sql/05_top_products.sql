-- Best-selling products from purchase events, ranked by revenue inside each category.
-- items is a repeated field, so UNNEST turns one purchase into one row per product.
WITH sold AS (
  SELECT
    item.item_category AS category,
    item.item_name AS product,
    item.quantity AS units,
    item.item_revenue_in_usd AS item_revenue_usd
  FROM `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`, UNNEST(items) AS item
  WHERE _TABLE_SUFFIX BETWEEN '20201101' AND '20210131'
    AND event_name = 'purchase'
    AND item.item_name NOT IN ('(not set)', '<Other>', '')  -- placeholders in the obfuscated sample
)
SELECT
  category,
  product,
  SUM(units) AS total_units,
  ROUND(SUM(item_revenue_usd), 2) AS total_revenue_usd,
  RANK() OVER (PARTITION BY category ORDER BY SUM(item_revenue_usd) DESC) AS rank_in_category
FROM sold
GROUP BY category, product
QUALIFY rank_in_category <= 5
ORDER BY total_revenue_usd DESC
