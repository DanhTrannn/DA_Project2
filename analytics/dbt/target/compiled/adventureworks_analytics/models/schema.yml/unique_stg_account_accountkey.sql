
    
    

select
    accountkey as unique_field,
    count(*) as n_records

from "AdventureworksDW"."staging"."stg_account"
where accountkey is not null
group by accountkey
having count(*) > 1


