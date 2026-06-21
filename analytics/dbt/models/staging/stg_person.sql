select
    businessentityid as business_entity_id,
    persontype as person_type,
    namestyle as name_style,
    title,
    firstname as first_name,
    middlename as middle_name,
    lastname as last_name,
    suffix,
    emailpromotion as email_promotion,
    rowguid,
    modifieddate as modified_at
from {{ source('oltp_person', 'person') }}
