
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select sales_order_id
from "Adventureworks"."core_dw"."fact_sales_order"
where sales_order_id is null



  
  
      
    ) dbt_internal_test