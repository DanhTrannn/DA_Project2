
    
    

select
    month as unique_field,
    count(*) as n_records

from "Adventureworks"."mart_sales_forecast"."monthly_sales_series"
where month is not null
group by month
having count(*) > 1


