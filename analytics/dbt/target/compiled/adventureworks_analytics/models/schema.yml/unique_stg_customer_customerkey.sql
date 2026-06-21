
    
    

select
    customerkey as unique_field,
    count(*) as n_records

from "AdventureworksDW"."staging"."stg_customer"
where customerkey is not null
group by customerkey
having count(*) > 1


