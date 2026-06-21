
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select product_key
from "Adventureworks"."core_dw"."fact_sales_order_line"
where product_key is null



  
  
      
    ) dbt_internal_test