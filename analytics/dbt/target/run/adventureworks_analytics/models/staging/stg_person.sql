
  create view "Adventureworks"."staging"."stg_person__dbt_tmp"
    
    
  as (
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
from "Adventureworks"."person"."person"
  );