
    
    

select
    productkey as unique_field,
    count(*) as n_records

from "AdventureworksDW"."staging"."stg_product"
where productkey is not null
group by productkey
having count(*) > 1


