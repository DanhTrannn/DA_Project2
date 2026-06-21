
    
    

select
    productcategorykey as unique_field,
    count(*) as n_records

from "AdventureworksDW"."staging"."stg_product_category"
where productcategorykey is not null
group by productcategorykey
having count(*) > 1


