
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    territory_id as unique_field,
    count(*) as n_records

from "Adventureworks"."staging"."stg_sales_territory"
where territory_id is not null
group by territory_id
having count(*) > 1



  
  
      
    ) dbt_internal_test