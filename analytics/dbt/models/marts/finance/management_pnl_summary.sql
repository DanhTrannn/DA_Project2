with totals as (
    select
        sum(revenue) as revenue,
        sum(estimated_cogs) as estimated_cogs,
        sum(estimated_gross_profit) as estimated_gross_profit,
        sum(loss_amount) as loss_amount
    from {{ ref('management_pnl_monthly') }}
)

select 1 as line_item_order, 'Doanh thu'::text as line_item, revenue as amount
from totals
union all
select 2, 'Giá vốn ước tính', estimated_cogs
from totals
union all
select 3, 'Lợi nhuận gộp ước tính', estimated_gross_profit
from totals
union all
select 4, 'Giá trị lỗ ở các dòng bán dưới giá vốn', loss_amount
from totals

