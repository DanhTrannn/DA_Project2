select
    c.customer_key,
    c.customer_name,
    c.customer_type,
    c.country_code,
    c.territory_name,
    min(f.order_date) as first_order_date,
    max(f.order_date) as last_order_date,
    count(distinct f.sales_order_id) as order_count,
    sum(f.order_quantity) as quantity_sold,
    sum(f.net_sales) as revenue,
    sum(f.estimated_gross_profit) as estimated_gross_profit,
    case when sum(f.net_sales) = 0 then null
         else sum(f.estimated_gross_profit) / sum(f.net_sales)
    end as estimated_gross_margin_pct,
    sum(f.net_sales) / nullif(count(distinct f.sales_order_id), 0) as average_order_value
from "Adventureworks"."core_dw"."dim_customer" c
left join "Adventureworks"."core_dw"."fact_sales_order_line" f
    using (customer_key)
group by 1, 2, 3, 4, 5