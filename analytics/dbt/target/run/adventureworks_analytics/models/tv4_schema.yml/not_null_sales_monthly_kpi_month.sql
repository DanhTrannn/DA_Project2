
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select month
from "Adventureworks"."mart_sales"."sales_monthly_kpi"
where month is null



  
  
      
    ) dbt_internal_test