
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select financekey
from "AdventureworksDW"."staging"."stg_finance"
where financekey is null



  
  
      
    ) dbt_internal_test