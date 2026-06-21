
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select source_url
from "Adventureworks"."mart_macro"."macro_observation_standardized"
where source_url is null



  
  
      
    ) dbt_internal_test