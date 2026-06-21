
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select accountkey
from "AdventureworksDW"."staging"."stg_account"
where accountkey is null



  
  
      
    ) dbt_internal_test