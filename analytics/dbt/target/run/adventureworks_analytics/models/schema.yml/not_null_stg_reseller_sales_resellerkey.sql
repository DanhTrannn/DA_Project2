
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select resellerkey
from "AdventureworksDW"."staging"."stg_reseller_sales"
where resellerkey is null



  
  
      
    ) dbt_internal_test