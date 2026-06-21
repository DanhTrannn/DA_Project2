with macro_by_country_year as (
    select
        country_code,
        country_name,
        year,
        max(indicator_value) filter (
            where indicator_code = 'FP.CPI.TOTL.ZG'
        ) as inflation_pct,
        max(indicator_value) filter (
            where indicator_code = 'NY.GDP.MKTP.KD.ZG'
        ) as gdp_growth_pct,
        max(indicator_value) filter (
            where indicator_code = 'SL.UEM.TOTL.ZS'
        ) as unemployment_pct,
        count(distinct indicator_code) as available_indicator_count,
        max(retrieved_at) as macro_retrieved_at
    from {{ ref('macro_observation_standardized') }}
    group by 1, 2, 3
)

select
    k.country_code,
    m.country_name,
    k.year,
    k.order_count,
    k.quantity_sold,
    k.revenue,
    k.estimated_cogs,
    k.estimated_gross_profit,
    k.estimated_gross_margin_pct,
    k.loss_amount,
    k.average_order_value,
    m.inflation_pct,
    m.gdp_growth_pct,
    m.unemployment_pct,
    coalesce(m.available_indicator_count, 0) as available_indicator_count,
    m.macro_retrieved_at,
    case
        when m.country_code is null then 'missing_macro_data'
        when m.available_indicator_count < 3 then 'partial_macro_data'
        else 'complete'
    end as macro_coverage_status,
    'Descriptive context only; correlation does not establish causation.'::text as analysis_caveat
from {{ ref('sales_country_year_kpi') }} k
left join macro_by_country_year m
    using (country_code, year)

