
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select metric_name
from "Adventureworks"."audit"."source_to_dw_reconciliation"
where metric_name is null



  
  
      
    ) dbt_internal_test