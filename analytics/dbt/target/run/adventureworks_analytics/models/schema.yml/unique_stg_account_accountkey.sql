
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    accountkey as unique_field,
    count(*) as n_records

from "AdventureworksDW"."staging"."stg_account"
where accountkey is not null
group by accountkey
having count(*) > 1



  
  
      
    ) dbt_internal_test