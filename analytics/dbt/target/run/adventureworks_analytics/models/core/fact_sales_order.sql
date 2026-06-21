
  
    

  create  table "Adventureworks"."core_dw"."fact_sales_order__dbt_tmp"
  
  
    as
  
  (
    select
    h.sales_order_id,
    to_char(h.order_date, 'YYYYMMDD')::integer as order_date_key,
    case when h.ship_date is null then null
         else to_char(h.ship_date, 'YYYYMMDD')::integer
    end as ship_date_key,
    h.order_date,
    h.due_date,
    h.ship_date,
    h.customer_id as customer_key,
    h.territory_id as geography_key,
    h.sales_person_id,
    h.order_status,
    h.is_online_order,
    h.subtotal,
    h.tax_amount,
    h.freight,
    h.total_due,
    h.fulfillment_days,
    h.is_late,
    current_timestamp as dw_loaded_at
from "Adventureworks"."staging"."stg_sales_order_header" h
  );
  