
  create view "Adventureworks"."staging"."stg_customer__dbt_tmp"
    
    
  as (
    select
    customerid as customer_id,
    personid as person_id,
    storeid as store_id,
    territoryid as territory_id,
    rowguid,
    modifieddate as modified_at
from "Adventureworks"."sales"."customer"
  );