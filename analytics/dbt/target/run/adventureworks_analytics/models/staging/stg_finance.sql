
  create view "AdventureworksDW"."staging"."stg_finance__dbt_tmp"
    
    
  as (
    select *
from "AdventureworksDW"."dbo"."factfinance"
  );