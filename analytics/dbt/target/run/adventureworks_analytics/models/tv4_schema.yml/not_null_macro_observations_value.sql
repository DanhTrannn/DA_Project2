
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select value
from "Adventureworks"."raw_macro"."macro_observations"
where value is null



  
  
      
    ) dbt_internal_test