
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select business_entity_id
from "Adventureworks"."staging"."stg_employee"
where business_entity_id is null



  
  
      
    ) dbt_internal_test