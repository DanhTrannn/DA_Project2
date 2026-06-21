
    
    

select
    metric_name as unique_field,
    count(*) as n_records

from "Adventureworks"."audit"."source_to_dw_reconciliation"
where metric_name is not null
group by metric_name
having count(*) > 1


