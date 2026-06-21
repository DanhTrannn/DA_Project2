
  create view "Adventureworks"."staging"."stg_sales_territory__dbt_tmp"
    
    
  as (
    select
    territoryid as territory_id,
    name as territory_name,
    countryregioncode as country_region_code,
    "group" as territory_group,
    salesytd as sales_ytd,
    saleslastyear as sales_last_year,
    costytd as cost_ytd,
    costlastyear as cost_last_year,
    rowguid,
    modifieddate as modified_at
from "Adventureworks"."sales"."salesterritory"
  );