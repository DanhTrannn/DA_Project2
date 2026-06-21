
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select salesordernumber
from "AdventureworksDW"."staging"."stg_internet_sales"
where salesordernumber is null



  
  
      
    ) dbt_internal_test