with metric_values as (
    select
        'sales_order_count'::text as metric_name,
        (select count(*)::numeric from "Adventureworks"."staging"."stg_sales_order_header") as source_value,
        (select count(*)::numeric from "Adventureworks"."core_dw"."fact_sales_order") as dw_value,
        0::numeric as tolerance

    union all

    select
        'sales_line_count',
        (select count(*)::numeric from "Adventureworks"."staging"."stg_sales_order_detail"),
        (select count(*)::numeric from "Adventureworks"."core_dw"."fact_sales_order_line"),
        0::numeric

    union all

    select
        'sales_line_revenue',
        (select round(sum(line_total)::numeric, 2) from "Adventureworks"."staging"."stg_sales_order_detail"),
        (select round(sum(net_sales)::numeric, 2) from "Adventureworks"."core_dw"."fact_sales_order_line"),
        0.01::numeric

    union all

    select
        'header_subtotal_vs_detail',
        (select round(sum(subtotal)::numeric, 2) from "Adventureworks"."staging"."stg_sales_order_header"),
        (select round(sum(net_sales)::numeric, 2) from "Adventureworks"."core_dw"."fact_sales_order_line"),
        0.01::numeric
)

select
    metric_name,
    source_value,
    dw_value,
    dw_value - source_value as difference,
    case when source_value = 0 then null
         else (dw_value - source_value) / source_value
    end as difference_pct,
    tolerance,
    case when abs(dw_value - source_value) <= tolerance then 'PASS' else 'FAIL' end as status,
    current_timestamp as checked_at
from metric_values