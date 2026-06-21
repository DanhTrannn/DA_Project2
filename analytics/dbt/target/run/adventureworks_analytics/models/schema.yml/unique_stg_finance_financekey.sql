
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    financekey as unique_field,
    count(*) as n_records

from "AdventureworksDW"."staging"."stg_finance"
where financekey is not null
group by financekey
having count(*) > 1



  
  
      
    ) dbt_internal_test