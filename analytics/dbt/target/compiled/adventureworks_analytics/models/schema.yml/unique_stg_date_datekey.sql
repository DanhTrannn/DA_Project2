
    
    

select
    datekey as unique_field,
    count(*) as n_records

from "AdventureworksDW"."staging"."stg_date"
where datekey is not null
group by datekey
having count(*) > 1


