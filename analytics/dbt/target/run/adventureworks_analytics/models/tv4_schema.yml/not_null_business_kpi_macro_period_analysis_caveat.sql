
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select analysis_caveat
from "Adventureworks"."mart_macro"."business_kpi_macro_period"
where analysis_caveat is null



  
  
      
    ) dbt_internal_test