
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select salesamount
from "AdventureworksDW"."staging"."stg_internet_sales"
where salesamount is null



  
  
      
    ) dbt_internal_test