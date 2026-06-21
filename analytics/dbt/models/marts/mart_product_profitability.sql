select
    d.product_id,
    p.product_number,
    p.product_name,
    sum(d.order_quantity) as quantity,
    sum(d.line_total) as revenue,
    sum(d.order_quantity * p.standard_cost) as estimated_product_cost,
    sum(d.line_total - d.order_quantity * p.standard_cost) as estimated_gross_profit
from {{ ref('stg_sales_order_detail') }} d
join {{ ref('stg_product') }} p using (product_id)
group by d.product_id, p.product_number, p.product_name
