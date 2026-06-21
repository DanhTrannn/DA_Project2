
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select line_total
from "Adventureworks"."staging"."stg_sales_order_detail"
where line_total is null



  
  
      
    ) dbt_internal_test