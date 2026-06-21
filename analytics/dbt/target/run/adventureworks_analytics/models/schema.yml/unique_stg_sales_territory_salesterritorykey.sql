
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    salesterritorykey as unique_field,
    count(*) as n_records

from "AdventureworksDW"."staging"."stg_sales_territory"
where salesterritorykey is not null
group by salesterritorykey
having count(*) > 1



  
  
      
    ) dbt_internal_test