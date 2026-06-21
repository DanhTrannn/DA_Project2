
  create view "AdventureworksDW"."staging"."stg_date__dbt_tmp"
    
    
  as (
    select *
from "AdventureworksDW"."dbo"."dimdate"
  );