
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select organizationkey
from "AdventureworksDW"."staging"."stg_organization"
where organizationkey is null



  
  
      
    ) dbt_internal_test