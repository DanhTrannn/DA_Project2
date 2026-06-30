select
    e.business_entity_id as salesperson_key,
    concat_ws(' ', p.first_name, p.middle_name, p.last_name) as salesperson_name,
    e.job_title,
    e.hire_date,
    e.is_salaried,
    e.is_current,
    current_timestamp as dw_loaded_at
from {{ ref('stg_employee') }} e
left join {{ ref('stg_person') }} p
    using (business_entity_id)
where e.job_title ilike '%sales%'

