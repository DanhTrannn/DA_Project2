
  create view "Adventureworks"."staging"."stg_product_subcategory__dbt_tmp"
    
    
  as (
    select
    productsubcategoryid as product_subcategory_id,
    productcategoryid as product_category_id,
    name as product_subcategory_name,
    rowguid,
    modifieddate as modified_at
from "Adventureworks"."production"."productsubcategory"
  );