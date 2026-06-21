
    
    

with all_values as (

    select
        status as value_field,
        count(*) as n_records

    from "Adventureworks"."audit"."data_quality_summary"
    group by status

)

select *
from all_values
where value_field not in (
    'PASS','WARN','FAIL'
)


