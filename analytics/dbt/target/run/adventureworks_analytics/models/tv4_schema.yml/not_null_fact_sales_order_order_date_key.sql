
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select order_date_key
from "Adventureworks"."core_dw"."fact_sales_order"
where order_date_key is null



  
  
      
    ) dbt_internal_test