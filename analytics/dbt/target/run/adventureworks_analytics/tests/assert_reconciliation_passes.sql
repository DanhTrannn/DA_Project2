
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  select *
from "Adventureworks"."audit"."source_to_dw_reconciliation"
where status <> 'PASS'
  
  
      
    ) dbt_internal_test