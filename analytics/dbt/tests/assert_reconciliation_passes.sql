select *
from {{ ref('source_to_dw_reconciliation') }}
where status <> 'PASS'

