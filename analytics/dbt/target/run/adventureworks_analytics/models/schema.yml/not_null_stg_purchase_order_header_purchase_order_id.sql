
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select purchase_order_id
from "Adventureworks"."staging"."stg_purchase_order_header"
where purchase_order_id is null



  
  
      
    ) dbt_internal_test