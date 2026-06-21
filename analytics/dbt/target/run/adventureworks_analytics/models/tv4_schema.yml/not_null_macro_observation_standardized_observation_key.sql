
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select observation_key
from "Adventureworks"."mart_macro"."macro_observation_standardized"
where observation_key is null



  
  
      
    ) dbt_internal_test