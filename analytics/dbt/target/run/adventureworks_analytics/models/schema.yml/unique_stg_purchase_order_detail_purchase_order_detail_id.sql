
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    purchase_order_detail_id as unique_field,
    count(*) as n_records

from "Adventureworks"."staging"."stg_purchase_order_detail"
where purchase_order_detail_id is not null
group by purchase_order_detail_id
having count(*) > 1



  
  
      
    ) dbt_internal_test