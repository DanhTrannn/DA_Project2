
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select total_due
from "Adventureworks"."staging"."stg_sales_order_header"
where total_due is null



  
  
      
    ) dbt_internal_test