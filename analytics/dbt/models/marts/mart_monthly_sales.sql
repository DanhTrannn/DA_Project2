with sales_lines as (
    select
        h.sales_order_id,
        h.order_date,
        h.territory_id,
        d.order_quantity,
        d.line_total as revenue,
        d.order_quantity * p.standard_cost as estimated_product_cost,
        h.is_late
    from {{ ref('stg_sales_order_header') }} h
    join {{ ref('stg_sales_order_detail') }} d using (sales_order_id)
    join {{ ref('stg_product') }} p using (product_id)
)

select
    date_trunc('month', order_date)::date as month,
    territory_id,
    count(distinct sales_order_id) as order_count,
    sum(order_quantity) as quantity,
    sum(revenue) as revenue,
    sum(estimated_product_cost) as estimated_product_cost,
    sum(revenue - estimated_product_cost) as estimated_gross_profit,
    avg(is_late::integer) as late_order_line_rate
from sales_lines
group by month, territory_id
