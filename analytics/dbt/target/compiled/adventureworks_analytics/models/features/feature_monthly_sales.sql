select
    month,
    order_count,
    quantity_sold as quantity,
    revenue,
    estimated_cogs,
    estimated_gross_profit,
    estimated_gross_margin_pct
from "Adventureworks"."mart_sales_forecast"."monthly_sales_series"
order by month