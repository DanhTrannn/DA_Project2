
  
    

  create  table "Adventureworks"."core_dw"."dim_customer__dbt_tmp"
  
  
    as
  
  (
    select
    c.customer_id as customer_key,
    c.customer_id,
    c.person_id,
    c.store_id,
    c.territory_id,
    case
        when c.person_id is not null then 'individual'
        when c.store_id is not null then 'store'
        else 'unknown'
    end as customer_type,
    coalesce(
        nullif(trim(concat_ws(' ', p.first_name, p.middle_name, p.last_name)), ''),
        s.store_name,
        'Customer ' || c.customer_id::text
    ) as customer_name,
    s.store_name,
    t.territory_name,
    t.country_region_code as country_code,
    t.territory_group
from "Adventureworks"."staging"."stg_customer" c
left join "Adventureworks"."staging"."stg_person" p
    on c.person_id = p.business_entity_id
left join "Adventureworks"."staging"."stg_store" s
    on c.store_id = s.business_entity_id
left join "Adventureworks"."staging"."stg_sales_territory" t
    using (territory_id)
  );
  