
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select interpretation_caveat
from "Adventureworks"."analytics"."macro_kpi_relation"
where interpretation_caveat is null



  
  
      
    ) dbt_internal_test