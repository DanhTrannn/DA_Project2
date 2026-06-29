\pset pager off

\echo '=== TV3 output row counts ==='
select 'sales_forecast' as table_name, count(*) as row_count
from analytics.sales_forecast
union all
select 'sales_forecast_metric', count(*)
from analytics.sales_forecast_metric
union all
select 'sales_forecast_decomposition', count(*)
from analytics.sales_forecast_decomposition
union all
select 'sales_forecast_scenario', count(*)
from analytics.sales_forecast_scenario
union all
select 'sales_forecast_summary', count(*)
from analytics.sales_forecast_summary
order by table_name;

\echo '=== Model ranking (lower error is better) ==='
select
    model_rank,
    model_name,
    round(mae::numeric, 2) as mae,
    round(rmse::numeric, 2) as rmse,
    round((mape * 100)::numeric, 2) as mape_pct,
    round((wape * 100)::numeric, 2) as wape_pct,
    round((accuracy * 100)::numeric, 2) as accuracy_pct
from analytics.sales_forecast_metric
order by model_rank;

\echo '=== Executive forecast summary ==='
select
    current_month,
    round(current_revenue::numeric, 2) as current_revenue,
    next_month,
    round(next_month_forecast::numeric, 2) as next_month_forecast,
    round((growth_vs_current * 100)::numeric, 2) as growth_vs_current_pct,
    best_model,
    round((best_wape * 100)::numeric, 2) as best_wape_pct,
    round(forecast_accuracy_score::numeric, 2) as reliability_score,
    risk_level,
    recommendation
from analytics.sales_forecast_summary;

\echo '=== Six-month forecast from the selected model ==='
select
    month_start,
    model_name,
    round(forecast_lower::numeric, 2) as forecast_lower,
    round(forecast_revenue::numeric, 2) as forecast_revenue,
    round(forecast_upper::numeric, 2) as forecast_upper
from analytics.sales_forecast
where dataset_type = 'future'
order by month_start;

\echo '=== Forecast scenarios ==='
select
    month_start,
    scenario_name,
    round(forecast_revenue::numeric, 2) as forecast_revenue,
    model_name
from analytics.sales_forecast_scenario
order by month_start, scenario_name;
