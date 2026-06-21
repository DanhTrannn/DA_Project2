
    
    

select
    purchase_order_id as unique_field,
    count(*) as n_records

from "Adventureworks"."staging"."stg_purchase_order_header"
where purchase_order_id is not null
group by purchase_order_id
having count(*) > 1


