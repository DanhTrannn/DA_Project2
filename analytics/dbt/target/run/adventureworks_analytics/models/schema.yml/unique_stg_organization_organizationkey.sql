
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    organizationkey as unique_field,
    count(*) as n_records

from "AdventureworksDW"."staging"."stg_organization"
where organizationkey is not null
group by organizationkey
having count(*) > 1



  
  
      
    ) dbt_internal_test