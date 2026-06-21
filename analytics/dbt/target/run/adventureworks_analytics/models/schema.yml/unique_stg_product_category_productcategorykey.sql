
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    productcategorykey as unique_field,
    count(*) as n_records

from "AdventureworksDW"."staging"."stg_product_category"
where productcategorykey is not null
group by productcategorykey
having count(*) > 1



  
  
      
    ) dbt_internal_test