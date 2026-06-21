select
    customerid as customer_id,
    personid as person_id,
    storeid as store_id,
    territoryid as territory_id,
    rowguid,
    modifieddate as modified_at
from {{ source('oltp_sales', 'customer') }}
