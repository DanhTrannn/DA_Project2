with line_kpi as (
    select
        date_trunc('month', order_date)::date as month,
        geography_key,
        country_code,
        sum(net_sales) as revenue,
        sum(estimated_cogs) as estimated_cogs,
        sum(estimated_gross_profit) as estimated_gross_profit,
        sum(loss_amount) as loss_amount
    from "Adventureworks"."core_dw"."fact_sales_order_line"
    group by 1, 2, 3
),
order_kpi as (
    select
        date_trunc('month', o.order_date)::date as month,
        o.geography_key,
        sum(o.tax_amount) as tax_amount,
        sum(o.freight) as freight_amount,
        sum(o.total_due) as total_due
    from "Adventureworks"."core_dw"."fact_sales_order" o
    group by 1, 2
)

select
    l.month,
    l.country_code,
    l.geography_key as territory_id,
    l.revenue,
    l.estimated_cogs,
    l.estimated_gross_profit,
    case when l.revenue = 0 then null
         else l.estimated_gross_profit / l.revenue
    end as estimated_gross_margin_pct,
    l.loss_amount,
    o.tax_amount,
    o.freight_amount,
    o.total_due,
    'gross_level_only'::text as accounting_scope
from line_kpi l
join order_kpi o
    using (month, geography_key)