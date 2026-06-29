with source_bounds as (
    select max(order_date) as max_order_date
    from {{ ref('fact_sales_order_line') }}
),
monthly as (
    select
        s.*,
        extract(year from s.month)::integer as year,
        extract(month from s.month)::integer as month_number,
        'Tháng ' || to_char(s.month, 'MM') as month_name,
        case
            when s.month < date_trunc('month', b.max_order_date)::date then true
            when b.max_order_date = (
                date_trunc('month', b.max_order_date)
                + interval '1 month'
                - interval '1 day'
            )::date then true
            else false
        end as is_complete_month
    from {{ ref('monthly_sales_series') }} s
    cross join source_bounds b
)
select
    *,
    revenue - lag(revenue, 12) over (order by month) as revenue_yoy_change,
    case
        when lag(revenue, 12) over (order by month) = 0 then null
        else (
            revenue - lag(revenue, 12) over (order by month)
        ) / lag(revenue, 12) over (order by month)
    end as revenue_yoy_growth_pct
from monthly
order by month
