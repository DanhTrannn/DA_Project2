
  create view "Adventureworks"."staging"."stg_product_category__dbt_tmp"
    
    
  as (
    select
    productcategoryid as product_category_id,
    name as product_category_name,
    rowguid,
    modifieddate as modified_at
from "Adventureworks"."production"."productcategory"
  );