
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select product_category_id
from "Adventureworks"."staging"."stg_product_category"
where product_category_id is null



  
  
      
    ) dbt_internal_test