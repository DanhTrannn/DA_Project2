
    
    

select
    sales_order_id as unique_field,
    count(*) as n_records

from "Adventureworks"."staging"."stg_sales_order_header"
where sales_order_id is not null
group by sales_order_id
having count(*) > 1


