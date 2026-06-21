
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select vendor_name
from "Adventureworks"."staging"."stg_vendor"
where vendor_name is null



  
  
      
    ) dbt_internal_test