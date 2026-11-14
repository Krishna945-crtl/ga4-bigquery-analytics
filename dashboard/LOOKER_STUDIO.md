# Looker Studio dashboard: build guide

Build this after the pipeline has run once (it creates the tables below in the `ga4_analytics` dataset).
Takes about an hour. Three pages, all reading from the mart tables, never from the raw export.

## 1. Connect the data

1. Open [lookerstudio.google.com](https://lookerstudio.google.com) and create a **Blank report**.
2. Add data → **BigQuery** → *My projects* → your project → `ga4_analytics` → `mart_daily_kpis` → Add.
3. Repeat *Resource → Manage added data sources → Add a data source* for:
   `mart_rolling_trends`, `mart_funnel`, `mart_traffic_sources`, `mart_top_products`, `mart_revenue_inr`.
4. Leave data credentials as **Owner's credentials**, so people with the link can see the charts without BigQuery access.

## 2. Page 1: Overview

| Element | Data source | Setup |
|---|---|---|
| Date range control | `mart_daily_kpis` | Dimension `day`, default *Custom: 1 Nov 2020 – 31 Jan 2021* |
| Scorecard: Revenue (USD) | `mart_daily_kpis` | Metric `revenue_usd` (Sum) |
| Scorecard: Revenue (INR) | `mart_revenue_inr` | Metric `revenue_inr` (Sum) |
| Scorecard: Purchases | `mart_daily_kpis` | Metric `purchases` (Sum) |
| Scorecard: Conversion rate | `mart_daily_kpis` | Calculated field `SUM(purchase_sessions) / SUM(sessions)`, type *Percent* |
| Scorecard: Avg daily users | `mart_daily_kpis` | Metric `users` (Average) |
| Time series: users | `mart_rolling_trends` | Dimension `day`; metrics `users`, `users_7d_avg` |
| Time series: revenue | `mart_rolling_trends` | Dimension `day`; metrics `revenue_usd`, `revenue_7d_avg` |

Why "avg daily users" and not "total users": the same person can visit on many days, so adding up
daily users counts them again. The true total (distinct users) is in the README results table.

## 3. Page 2: Funnel and channels

| Element | Data source | Setup |
|---|---|---|
| Funnel | `mart_funnel` | Bar chart, horizontal. Dimension `step`, metric `users`, sort by `step_order` ascending. Show data labels. |
| Drop-off table | `mart_funnel` | Table: `step`, `users`, `pct_of_first_step`, `pct_of_previous_step` |
| Channel table | `mart_traffic_sources` | Table: `source`, `medium`, `users`, `buyers`, `buyer_rate_pct`, `revenue_usd`. Sort by `users` desc. Add a heatmap on `buyer_rate_pct`. |
| Note text box | – | "Source = the channel that first acquired the user (GA4 first touch)." |

## 4. Page 3: Products and revenue in INR

| Element | Data source | Setup |
|---|---|---|
| Top products bar | `mart_top_products` | Dimension `product`, metric `total_revenue_usd`, top 10 |
| Category filter | `mart_top_products` | Drop-down control on `category` |
| INR revenue time series | `mart_revenue_inr` | Dimension `day`; metric `revenue_inr` |
| Rate table | `mart_revenue_inr` | Table: `day`, `usd_inr`, `rate_carried_forward` (shows weekend days that reuse Friday's rate) |

## 5. Style

- Theme: *Constellation* or a plain light theme; one accent colour for all "main" metrics, grey for 7-day averages.
- Title on every chart says what it answers ("Where users drop off"), not the table name.
- Keep every page to one screen without scrolling.

## 6. Share it

1. **Share → Manage access → Link settings → Anyone with the link can view.**
2. Paste the link in the README (top of the page) and on the resume.
3. Take one screenshot of Page 1, save it as `dashboard/overview.png`, and add it to the README.

> BigQuery sandbox tables expire after 60 days. If the dashboard shows "no data" later, run the Colab
> notebook again; it rebuilds the same tables and the dashboard picks them up.
