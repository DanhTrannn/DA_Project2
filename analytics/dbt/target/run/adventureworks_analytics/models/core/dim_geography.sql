
  
    

  create  table "Adventureworks"."core_dw"."dim_geography__dbt_tmp"
  
  
    as
  
  (
    select
    territory_id as geography_key,
    territory_id,
    territory_name,
    country_region_code as country_code,
    territory_group,
    sales_ytd,
    sales_last_year
from "Adventureworks"."staging"."stg_sales_territory"
  );
  