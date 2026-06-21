
    
    

select
    financekey as unique_field,
    count(*) as n_records

from "AdventureworksDW"."staging"."stg_finance"
where financekey is not null
group by financekey
having count(*) > 1


