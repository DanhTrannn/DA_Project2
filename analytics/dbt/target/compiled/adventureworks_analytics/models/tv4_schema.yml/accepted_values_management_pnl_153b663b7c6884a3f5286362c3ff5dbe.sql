
    
    

with all_values as (

    select
        accounting_scope as value_field,
        count(*) as n_records

    from "Adventureworks"."mart_finance"."management_pnl_monthly"
    group by accounting_scope

)

select *
from all_values
where value_field not in (
    'gross_level_only'
)


