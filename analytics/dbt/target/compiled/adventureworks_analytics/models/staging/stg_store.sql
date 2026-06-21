select
    businessentityid as business_entity_id,
    name as store_name,
    salespersonid as sales_person_id,
    rowguid,
    modifieddate as modified_at
from "Adventureworks"."sales"."store"