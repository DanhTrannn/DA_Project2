
  
    

  create  table "Adventureworks"."mart_product"."product_sales_summary__dbt_tmp"
  
  
    as
  
  (
    select
    p.product_key,
    p.product_number,
    p.product_name,
    p.product_subcategory_name,
    p.product_category_name,
    sum(f.order_quantity) as quantity_sold,
    sum(f.net_sales) as revenue,
    sum(f.estimated_cogs) as estimated_cogs,
    sum(f.estimated_gross_profit) as estimated_gross_profit,
    case when sum(f.net_sales) = 0 then null
         else sum(f.estimated_gross_profit) / sum(f.net_sales)
    end as estimated_gross_margin_pct,
    sum(f.loss_amount) as loss_amount
from "Adventureworks"."core_dw"."dim_product" p
left join "Adventureworks"."core_dw"."fact_sales_order_line" f
    using (product_key)
group by 1, 2, 3, 4, 5
  );
  