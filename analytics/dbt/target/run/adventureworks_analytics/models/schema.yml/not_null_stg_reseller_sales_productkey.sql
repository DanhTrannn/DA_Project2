
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select productkey
from "AdventureworksDW"."staging"."stg_reseller_sales"
where productkey is null



  
  
      
    ) dbt_internal_test