
    
    

select
    customer_key as unique_field,
    count(*) as n_records

from "Adventureworks"."mart_customer"."customer_base"
where customer_key is not null
group by customer_key
having count(*) > 1


