
    
    

select
    organizationkey as unique_field,
    count(*) as n_records

from "AdventureworksDW"."staging"."stg_organization"
where organizationkey is not null
group by organizationkey
having count(*) > 1


