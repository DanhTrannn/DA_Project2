
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select year
from "Adventureworks"."mart_sales"."sales_country_year_kpi"
where year is null



  
  
      
    ) dbt_internal_test