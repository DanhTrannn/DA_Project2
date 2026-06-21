
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select net_sales
from "Adventureworks"."core_dw"."fact_sales_order_line"
where net_sales is null



  
  
      
    ) dbt_internal_test