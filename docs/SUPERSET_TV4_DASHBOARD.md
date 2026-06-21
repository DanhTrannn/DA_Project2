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
7. Line: Revenue Growth % theo tháng.
8. Bar: Revenue/Gross Profit theo country.
9. Table: territory có loss amount hoặc margin thấp.

Filters: month, country_code, territory_id.

## 2. Data Quality and Reconciliation

Dataset:

- `audit.source_to_dw_reconciliation`
- `audit.data_quality_summary`

Charts:

1. Table: metric, source value, DW value, difference, status.
2. KPI: số reconciliation FAIL.
3. Bar: failed record count theo data-quality check.
4. Table: macro coverage warning.

## 3. Macro Context

Dataset:

- `mart_macro.business_kpi_macro_period`
- `analytics.macro_kpi_relation`

Charts:

1. Line: Revenue theo country/year.
2. Line: Inflation % theo country/year.
3. Dual-axis hoặc normalized line: Revenue Growth và Inflation.
4. Scatter: Inflation % và Revenue/Gross Margin.
5. Table: country, year, revenue, margin, CPI, GDP growth, unemployment.
6. Table: correlation, sample size, strength, caveat.

Filters: country_code, year.

Dashboard phải có ghi chú hiển thị:

> Macro indicators provide descriptive context only. Correlation does not
> establish a causal effect on AdventureWorks revenue or margin.

