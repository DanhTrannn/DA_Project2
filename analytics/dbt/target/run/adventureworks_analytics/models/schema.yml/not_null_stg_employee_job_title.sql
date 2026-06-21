
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select job_title
from "Adventureworks"."staging"."stg_employee"
where job_title is null



  
  
      
    ) dbt_internal_test