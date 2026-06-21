
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select country_code
from "Adventureworks"."mart_macro"."business_kpi_macro_period"
where country_code is null



  
  
      
    ) dbt_internal_test