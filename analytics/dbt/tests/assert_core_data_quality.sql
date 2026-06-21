select *
from {{ ref('data_quality_summary') }}
where status = 'FAIL'

