with base as (
    select *
    from {{ ref('business_kpi_macro_period') }}
    where available_indicator_count > 0
),
long_form as (
    select
        b.country_code,
        b.year,
        k.kpi_name,
        k.kpi_value,
        m.indicator_code,
        m.indicator_value
    from base b
    cross join lateral (
        values
            ('revenue', b.revenue::numeric),
            ('quantity_sold', b.quantity_sold::numeric),
            ('estimated_gross_margin_pct', b.estimated_gross_margin_pct::numeric),
            ('average_order_value', b.average_order_value::numeric)
    ) as k(kpi_name, kpi_value)
    cross join lateral (
        values
            ('FP.CPI.TOTL.ZG', b.inflation_pct::numeric),
            ('NY.GDP.MKTP.KD.ZG', b.gdp_growth_pct::numeric),
            ('SL.UEM.TOTL.ZS', b.unemployment_pct::numeric)
    ) as m(indicator_code, indicator_value)
    where k.kpi_value is not null
      and m.indicator_value is not null
),
country_relation as (
    select
        'country'::text as relation_scope,
        country_code,
        kpi_name,
        indicator_code,
        count(*) as sample_size,
        corr(kpi_value, indicator_value) as correlation
    from long_form
    group by 1, 2, 3, 4
),
all_market_relation as (
    select
        'all_markets'::text as relation_scope,
        null::text as country_code,
        kpi_name,
        indicator_code,
        count(*) as sample_size,
        corr(kpi_value, indicator_value) as correlation
    from long_form
    group by 1, 2, 3, 4
),
combined as (
    select * from country_relation
    union all
    select * from all_market_relation
)

select
    relation_scope,
    country_code,
    kpi_name,
    indicator_code,
    sample_size,
    correlation,
    case
        when correlation is null then 'insufficient_variation'
        when abs(correlation) >= 0.7 then 'strong'
        when abs(correlation) >= 0.4 then 'moderate'
        else 'weak'
    end as correlation_strength,
    'Descriptive correlation only. Small samples and omitted variables prevent causal claims.'::text
        as interpretation_caveat
from combined

