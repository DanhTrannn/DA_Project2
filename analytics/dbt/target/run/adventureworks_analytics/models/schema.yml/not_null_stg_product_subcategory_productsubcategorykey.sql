
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select productsubcategorykey
from "AdventureworksDW"."staging"."stg_product_subcategory"
where productsubcategorykey is null



  
  
      
    ) dbt_internal_test