
    
    

select
    product_subcategory_id as unique_field,
    count(*) as n_records

from "Adventureworks"."staging"."stg_product_subcategory"
where product_subcategory_id is not null
group by product_subcategory_id
having count(*) > 1


