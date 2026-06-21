
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    productsubcategorykey as unique_field,
    count(*) as n_records

from "AdventureworksDW"."staging"."stg_product_subcategory"
where productsubcategorykey is not null
group by productsubcategorykey
having count(*) > 1



  
  
      
    ) dbt_internal_test