
  create view "AdventureworksDW"."staging"."stg_organization__dbt_tmp"
    
    
  as (
    select *
from "AdventureworksDW"."dbo"."dimorganization"
  );