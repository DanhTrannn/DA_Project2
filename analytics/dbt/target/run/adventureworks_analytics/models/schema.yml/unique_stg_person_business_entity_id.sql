
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    business_entity_id as unique_field,
    count(*) as n_records

from "Adventureworks"."staging"."stg_person"
where business_entity_id is not null
group by business_entity_id
having count(*) > 1



  
  
      
    ) dbt_internal_test