
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select customerkey
from "AdventureworksDW"."staging"."stg_customer"
where customerkey is null



  
  
      
    ) dbt_internal_test