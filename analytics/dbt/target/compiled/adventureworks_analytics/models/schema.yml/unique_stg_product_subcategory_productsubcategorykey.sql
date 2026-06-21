
    
    

select
    productsubcategorykey as unique_field,
    count(*) as n_records

from "AdventureworksDW"."staging"."stg_product_subcategory"
where productsubcategorykey is not null
group by productsubcategorykey
having count(*) > 1


