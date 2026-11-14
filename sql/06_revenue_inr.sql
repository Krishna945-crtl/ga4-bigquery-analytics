-- Daily revenue in rupees: the daily KPI mart joined with USD -> INR rates from the Frankfurter API.
-- Needs the pipeline to run first, it creates both tables in the ga4_analytics dataset.
SELECT
  k.day,
  k.purchases,
  k.revenue_usd,
  fx.usd_inr,
  fx.is_filled AS rate_carried_forward,
  ROUND(k.revenue_usd * fx.usd_inr, 2) AS revenue_inr
FROM ga4_analytics.mart_daily_kpis AS k
LEFT JOIN ga4_analytics.fx_usd_inr AS fx
  ON fx.day = k.day
ORDER BY k.day
