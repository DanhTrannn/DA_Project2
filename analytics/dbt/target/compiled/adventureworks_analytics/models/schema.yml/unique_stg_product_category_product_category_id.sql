
    
    

select
    product_category_id as unique_field,
    count(*) as n_records

from "Adventureworks"."staging"."stg_product_category"
where product_category_id is not null
group by product_category_id
having count(*) > 1


