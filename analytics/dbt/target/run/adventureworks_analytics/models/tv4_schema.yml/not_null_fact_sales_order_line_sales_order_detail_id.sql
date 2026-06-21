
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select sales_order_detail_id
from "Adventureworks"."core_dw"."fact_sales_order_line"
where sales_order_detail_id is null



  
  
      
    ) dbt_internal_test