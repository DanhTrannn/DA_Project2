with reference_date as (
    select max(order_date) + 1 as value
    from {{ ref('fact_sales_order') }}
)

select
    c.customer_key,
    c.customer_name,
    c.customer_type,
    c.country_code,
    (select value from reference_date) - max(o.order_date) as recency_days,
    count(distinct o.sales_order_id) as frequency,
    sum(o.subtotal) as monetary,
    avg(o.subtotal) as average_order_value,
    min(o.order_date) as first_order_date,
    max(o.order_date) as last_order_date
from {{ ref('dim_customer') }} c
join {{ ref('fact_sales_order') }} o
    using (customer_key)
group by 1, 2, 3, 4

