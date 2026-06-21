
    
    

select
    territory_id as unique_field,
    count(*) as n_records

from "Adventureworks"."staging"."stg_sales_territory"
where territory_id is not null
group by territory_id
having count(*) > 1


