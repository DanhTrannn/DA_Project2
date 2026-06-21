
  
    

  create  table "Adventureworks"."mart_sales"."sales_country_year_kpi__dbt_tmp"
  
  
    as
  
  (
    select
    country_code,
    extract(year from order_date)::integer as year,
    count(distinct sales_order_id) as order_count,
    sum(order_quantity) as quantity_sold,
    sum(net_sales) as revenue,
    sum(estimated_cogs) as estimated_cogs,
    sum(estimated_gross_profit) as estimated_gross_profit,
    case when sum(net_sales) = 0 then null
         else sum(estimated_gross_profit) / sum(net_sales)
    end as estimated_gross_margin_pct,
    sum(loss_amount) as loss_amount,
    sum(net_sales) / nullif(count(distinct sales_order_id), 0) as average_order_value
from "Adventureworks"."core_dw"."fact_sales_order_line"
where country_code is not null
group by country_code, extract(year from order_date)
  );
  