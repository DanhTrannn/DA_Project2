
  create view "AdventureworksDW"."staging"."stg_account__dbt_tmp"
    
    
  as (
    select *
from "AdventureworksDW"."dbo"."dimaccount"
  );