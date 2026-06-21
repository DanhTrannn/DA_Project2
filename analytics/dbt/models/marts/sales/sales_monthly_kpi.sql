with monthly as (
    select
        date_trunc('month', f.order_date)::date as month,
        f.country_code,
        f.geography_key as territory_id,
        count(distinct f.sales_order_id) as order_count,
        count(*) as sales_line_count,
        sum(f.order_quantity) as quantity_sold,
        sum(f.gross_sales) as gross_sales,
        sum(f.discount_amount) as discount_amount,
        sum(f.net_sales) as revenue,
        sum(f.estimated_cogs) as estimated_cogs,
        sum(f.estimated_gross_profit) as estimated_gross_profit,
        case when sum(f.net_sales) = 0 then null
             else sum(f.estimated_gross_profit) / sum(f.net_sales)
        end as estimated_gross_margin_pct,
        sum(f.loss_amount) as loss_amount,
        count(*) filter (where f.is_loss_line) as loss_line_count,
        count(*) filter (where f.is_loss_line)::numeric / nullif(count(*), 0) as loss_line_rate,
        sum(f.net_sales) / nullif(count(distinct f.sales_order_id), 0) as average_order_value
    from {{ ref('fact_sales_order_line') }} f
    group by 1, 2, 3
)

select
    *,
    revenue - lag(revenue) over (
        partition by country_code, territory_id order by month
    ) as revenue_change,
    case
        when lag(revenue) over (
            partition by country_code, territory_id order by month
        ) = 0 then null
        else revenue / lag(revenue) over (
            partition by country_code, territory_id order by month
        ) - 1
    end as revenue_growth_pct
from monthly
