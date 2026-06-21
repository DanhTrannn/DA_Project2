
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    sales_order_detail_id as unique_field,
    count(*) as n_records

from "Adventureworks"."staging"."stg_sales_order_detail"
where sales_order_detail_id is not null
group by sales_order_detail_id
having count(*) > 1



  
  
      
    ) dbt_internal_test