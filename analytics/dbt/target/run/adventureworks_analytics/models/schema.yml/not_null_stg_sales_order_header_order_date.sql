
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select order_date
from "Adventureworks"."staging"."stg_sales_order_header"
where order_date is null



  
  
      
    ) dbt_internal_test