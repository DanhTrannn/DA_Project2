
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select full_date
from "Adventureworks"."core_dw"."dim_date"
where full_date is null



  
  
      
    ) dbt_internal_test