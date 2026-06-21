
  
    

  create  table "Adventureworks"."mart_sales_forecast"."monthly_sales_series__dbt_tmp"
  
  
    as
  
  (
    select
    date_trunc('month', order_date)::date as month,
    count(distinct sales_order_id) as order_count,
    sum(order_quantity) as quantity_sold,
    sum(net_sales) as revenue,
    sum(estimated_cogs) as estimated_cogs,
    sum(estimated_gross_profit) as estimated_gross_profit,
    case when sum(net_sales) = 0 then null
         else sum(estimated_gross_profit) / sum(net_sales)
    end as estimated_gross_margin_pct
from "Adventureworks"."core_dw"."fact_sales_order_line"
group by 1
order by 1
  );
  