
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select salesorderlinenumber
from "AdventureworksDW"."staging"."stg_reseller_sales"
where salesorderlinenumber is null



  
  
      
    ) dbt_internal_test