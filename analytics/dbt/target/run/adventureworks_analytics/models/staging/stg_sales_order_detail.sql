
  create view "Adventureworks"."staging"."stg_sales_order_detail__dbt_tmp"
    
    
  as (
    select
    salesorderdetailid as sales_order_detail_id,
    salesorderid as sales_order_id,
    carriertrackingnumber as carrier_tracking_number,
    orderqty as order_quantity,
    productid as product_id,
    specialofferid as special_offer_id,
    unitprice as unit_price,
    unitpricediscount as unit_price_discount,
    unitprice * orderqty * (1 - unitpricediscount) as line_total,
    rowguid,
    modifieddate as modified_at
from "Adventureworks"."sales"."salesorderdetail"
  );