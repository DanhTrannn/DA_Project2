with bounds as (
    select
        min(order_date) as min_date,
        max(order_date) as max_date
    from {{ ref('stg_sales_order_header') }}
),
dates as (
    select generate_series(min_date, max_date, interval '1 day')::date as full_date
    from bounds
)

select
    to_char(full_date, 'YYYYMMDD')::integer as date_key,
    full_date,
    extract(year from full_date)::integer as year,
    extract(quarter from full_date)::integer as quarter,
    extract(month from full_date)::integer as month,
    to_char(full_date, 'Month')::text as month_name,
    extract(isodow from full_date)::integer as day_of_week,
    to_char(full_date, 'Day')::text as day_name,
    date_trunc('month', full_date)::date as month_start_date,
    date_trunc('quarter', full_date)::date as quarter_start_date,
    extract(isodow from full_date) in (6, 7) as is_weekend
from dates

