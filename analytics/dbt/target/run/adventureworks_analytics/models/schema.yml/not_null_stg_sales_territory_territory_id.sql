
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select territory_id
from "Adventureworks"."staging"."stg_sales_territory"
where territory_id is null



  
  
      
    ) dbt_internal_test