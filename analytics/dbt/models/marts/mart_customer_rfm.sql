with orders as (
    select
        customer_id,
        sales_order_id,
        order_date,
        total_due as order_value
    from {{ ref('stg_sales_order_header') }}
),
reference_date as (
    select max(order_date) + 1 as value
    from orders
)

select
    customer_id,
    (select value from reference_date) - max(order_date) as recency_days,
    count(*) as frequency,
    sum(order_value) as monetary,
    avg(order_value) as average_order_value,
    min(order_date) as first_order_date,
    max(order_date) as last_order_date
from orders
group by customer_id
