select
    min(order_date) as data_start_date,
    max(order_date) as data_end_date,
    count(distinct sales_order_id) as order_count,
    count(*) as sales_line_count,
    sum(order_quantity) as quantity_sold,
    sum(net_sales) as revenue,
    sum(estimated_cogs) as estimated_cogs,
    sum(estimated_gross_profit) as estimated_gross_profit,
    case when sum(net_sales) = 0 then null
         else sum(estimated_gross_profit) / sum(net_sales)
    end as estimated_gross_margin_pct,
    sum(loss_amount) as loss_amount,
    count(*) filter (where is_loss_line) as loss_line_count,
    sum(net_sales) / nullif(count(distinct sales_order_id), 0) as average_order_value
from {{ ref('fact_sales_order_line') }}

