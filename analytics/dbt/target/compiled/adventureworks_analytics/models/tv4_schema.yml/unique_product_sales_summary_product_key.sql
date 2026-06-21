
    
    

select
    product_key as unique_field,
    count(*) as n_records

from "Adventureworks"."mart_product"."product_sales_summary"
where product_key is not null
group by product_key
having count(*) > 1


