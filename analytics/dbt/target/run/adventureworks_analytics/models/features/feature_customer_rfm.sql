
  
    

  create  table "Adventureworks"."analytics"."feature_customer_rfm__dbt_tmp"
  
  
    as
  
  (
    select *
from "Adventureworks"."mart_customer"."customer_rfm"
  );
  