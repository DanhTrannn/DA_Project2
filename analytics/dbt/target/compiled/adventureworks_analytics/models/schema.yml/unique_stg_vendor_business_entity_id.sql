
    
    

select
    business_entity_id as unique_field,
    count(*) as n_records

from "Adventureworks"."staging"."stg_vendor"
where business_entity_id is not null
group by business_entity_id
having count(*) > 1


