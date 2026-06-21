
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select salesterritorykey
from "AdventureworksDW"."staging"."stg_sales_territory"
where salesterritorykey is null



  
  
      
    ) dbt_internal_test