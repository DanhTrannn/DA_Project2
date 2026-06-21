
    
    

select
    sales_order_detail_id as unique_field,
    count(*) as n_records

from "Adventureworks"."core_dw"."fact_sales_order_line"
where sales_order_detail_id is not null
group by sales_order_detail_id
having count(*) > 1


