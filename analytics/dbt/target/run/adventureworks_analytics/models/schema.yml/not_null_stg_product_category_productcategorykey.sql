
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select productcategorykey
from "AdventureworksDW"."staging"."stg_product_category"
where productcategorykey is null



  
  
      
    ) dbt_internal_test