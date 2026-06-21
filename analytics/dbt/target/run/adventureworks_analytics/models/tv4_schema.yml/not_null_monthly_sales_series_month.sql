
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select month
from "Adventureworks"."mart_sales_forecast"."monthly_sales_series"
where month is null



  
  
      
    ) dbt_internal_test