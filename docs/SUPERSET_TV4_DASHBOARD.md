# Superset Dashboard Spec - TV4

Superset kết nối database `Adventureworks`. Dataset phải đọc từ DataMart/audit,
không đọc trực tiếp bảng OLTP.

## 1. Executive Overview

Dataset:

- `mart_sales.executive_kpi`
- `mart_sales.sales_monthly_kpi`
- `mart_finance.management_pnl_monthly`

Charts:

1. KPI Revenue.
2. KPI Estimated Gross Profit.
3. KPI Estimated Gross Margin %.
4. KPI Order Count.
5. KPI Loss Amount.
6. Line: Revenue và Gross Profit theo tháng.
7. Bar: P&L gross-level gồm Revenue, Estimated COGS, Estimated Gross Profit
   và Loss Amount.

Filters: month, country_code, territory_id.

## 2. Data Quality and Reconciliation

Dataset:

- `audit.source_to_dw_reconciliation`
- `audit.data_quality_summary`

Charts:

1. Table: metric, source value, DW value, difference, status.
2. Table: model, data-quality check, failed record count và status.

## 3. Macro Context

Dataset:

- `mart_macro.business_kpi_macro_period`
- `analytics.macro_kpi_relation`

Charts:

1. Line: Revenue theo country/year.
2. Line: Inflation, GDP growth và unemployment theo year.
3. Table: country, year, revenue, margin, CPI, GDP growth, unemployment và
   trạng thái coverage.
4. Table: correlation, sample size, strength và caveat.

Filters: country_code, year.

Dashboard có 13 chart, được chia thành bốn phần bằng narrative Markdown. Phần
Macro hiển thị ghi chú:

> Macro indicators provide descriptive context only. Correlation does not
> establish a causal effect on AdventureWorks revenue or margin.

URL ổn định:

`http://localhost:8088/superset/dashboard/adventureworks-tv4-executive-macro/`
