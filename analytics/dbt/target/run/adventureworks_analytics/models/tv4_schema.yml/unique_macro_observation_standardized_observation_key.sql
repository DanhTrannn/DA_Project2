
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    observation_key as unique_field,
    count(*) as n_records

from "Adventureworks"."mart_macro"."macro_observation_standardized"
where observation_key is not null
group by observation_key
having count(*) > 1



  
  
      
    ) dbt_internal_test