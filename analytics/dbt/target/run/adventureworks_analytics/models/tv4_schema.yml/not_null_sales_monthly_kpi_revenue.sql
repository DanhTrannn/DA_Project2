
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select revenue
from "Adventureworks"."mart_sales"."sales_monthly_kpi"
where revenue is null



  
  
      
    ) dbt_internal_test