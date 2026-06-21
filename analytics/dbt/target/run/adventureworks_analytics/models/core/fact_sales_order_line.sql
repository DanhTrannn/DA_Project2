
  
    

  create  table "Adventureworks"."core_dw"."fact_sales_order_line__dbt_tmp"
  
  
    as
  
  (
    select
    d.sales_order_detail_id,
    d.sales_order_id,
    to_char(h.order_date, 'YYYYMMDD')::integer as order_date_key,
    h.order_date,
    h.customer_id as customer_key,
    h.territory_id as geography_key,
    t.country_region_code as country_code,
    d.product_id as product_key,
    d.special_offer_id,
    d.order_quantity,
    d.unit_price,
    d.unit_price_discount,
    d.order_quantity * d.unit_price as gross_sales,
    d.order_quantity * d.unit_price * d.unit_price_discount as discount_amount,
    d.line_total as net_sales,
    d.order_quantity * p.standard_cost as estimated_cogs,
    d.line_total - (d.order_quantity * p.standard_cost) as estimated_gross_profit,
    case when d.line_total = 0 then null
         else (d.line_total - (d.order_quantity * p.standard_cost)) / d.line_total
    end as estimated_gross_margin_pct,
    d.line_total < (d.order_quantity * p.standard_cost) as is_loss_line,
    greatest((d.order_quantity * p.standard_cost) - d.line_total, 0) as loss_amount,
    h.is_online_order,
    h.is_late,
    current_timestamp as dw_loaded_at
from "Adventureworks"."staging"."stg_sales_order_detail" d
join "Adventureworks"."staging"."stg_sales_order_header" h
    using (sales_order_id)
join "Adventureworks"."staging"."stg_product" p
    using (product_id)
left join "Adventureworks"."staging"."stg_sales_territory" t
    using (territory_id)
  );
  