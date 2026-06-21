
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  select *
from "Adventureworks"."audit"."data_quality_summary"
where status = 'FAIL'
  
  
      
    ) dbt_internal_test