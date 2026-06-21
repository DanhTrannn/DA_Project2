select
    businessentityid as business_entity_id,
    accountnumber as account_number,
    name as vendor_name,
    creditrating as credit_rating,
    preferredvendorstatus as is_preferred_vendor,
    activeflag as is_active,
    purchasingwebserviceurl as purchasing_web_service_url,
    modifieddate as modified_at
from "Adventureworks"."purchasing"."vendor"