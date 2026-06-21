# TV4 KPI Dictionary

| KPI | Công thức | Grain chính | Nguồn | Diễn giải |
|---|---|---|---|---|
| Gross Sales | `sum(order_quantity * unit_price)` | month/country/territory | `core_dw.fact_sales_order_line` | Giá bán trước chiết khấu |
| Discount Amount | `sum(quantity * price * discount)` | month/country/territory | `core_dw.fact_sales_order_line` | Giá trị chiết khấu |
| Revenue | `sum(net_sales)` | month/country/territory | `core_dw.fact_sales_order_line` | Doanh thu dòng bán sau chiết khấu |
| Estimated COGS | `sum(quantity * standard_cost)` | month/country/territory | fact sales line + product standard cost | Giá vốn ước tính |
| Estimated Gross Profit | `revenue - estimated_cogs` | month/country/territory | `mart_sales.sales_monthly_kpi` | Lợi nhuận gộp quản trị |
| Estimated Gross Margin % | `gross_profit / revenue` | month/country/territory | `mart_sales.sales_monthly_kpi` | Biên lợi nhuận gộp |
| Loss Amount | `sum(max(cogs - revenue, 0))` | month/country/territory | `core_dw.fact_sales_order_line` | Giá trị lỗ ở các dòng có gross profit âm |
| Loss Line Rate | `loss_line_count / sales_line_count` | month/country/territory | `mart_sales.sales_monthly_kpi` | Tỷ lệ dòng bán lỗ |
| Average Order Value | `revenue / distinct_order_count` | month/country/territory | `mart_sales.sales_monthly_kpi` | Giá trị đơn trung bình |
| Revenue Growth % | `current_revenue / previous_revenue - 1` | month/country/territory | `mart_sales.sales_monthly_kpi` | Tăng trưởng so với tháng trước trong cùng territory |
| Reconciliation Difference | `dw_value - source_value` | metric/run | `audit.source_to_dw_reconciliation` | Chênh lệch nguồn và DW |
| Inflation % | World Bank `FP.CPI.TOTL.ZG` | country/year | `raw_macro.macro_observations` | Tăng CPI tiêu dùng hằng năm |
| GDP Growth % | World Bank `NY.GDP.MKTP.KD.ZG` | country/year | `raw_macro.macro_observations` | Tăng trưởng GDP thực |
| Unemployment % | World Bank `SL.UEM.TOTL.ZS` | country/year | `raw_macro.macro_observations` | Tỷ lệ thất nghiệp |

## Accounting scope

`mart_finance.management_pnl_monthly` là P&L quản trị ở mức gross-level. Nó
không phải báo cáo lợi nhuận ròng vì AdventureWorks thiếu chi phí bán hàng,
chi phí quản lý, lãi vay, thuế thu nhập và sổ cái hoàn chỉnh.

