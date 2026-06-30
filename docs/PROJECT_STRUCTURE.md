# Project Structure - AdventureWorks Analytics

## Kiến trúc dữ liệu

```text
AdventureWorks OLTP
        -> staging
        -> Core DW
        -> DataMart
        -> Superset / Analytics models
        -> Streamlit / Report
```

Dashboard và model đọc từ DW/DataMart/analytics để dùng chung grain và công
thức KPI, không tự join trực tiếp OLTP.

## Thư mục chính

| Đường dẫn | Vai trò |
|---|---|
| `data/`, `install.sql` | Dữ liệu và quy trình import AdventureWorks |
| `analytics/dbt/models/staging/` | Chuẩn hóa bảng nguồn |
| `analytics/dbt/models/core/` | Dimension và fact dùng chung |
| `analytics/dbt/models/marts/` | DataMart nghiệp vụ |
| `analytics/dbt/models/features/` | Feature đầu vào model |
| `analytics/dbt/models/audit/` | Reconciliation và data quality |
| `analytics/src/aw_analytics/` | Code Data Mining |
| `analytics/streamlit/` | Giao diện kết quả model |
| `superset/` | Bootstrap dashboard BI |
| `docs/` | Hướng dẫn, KPI và bàn giao |

## Schema PostgreSQL

| Schema | Nội dung |
|---|---|
| `staging` | 13 view chuẩn hóa OLTP |
| `core_dw` | date/customer/product/geography/salesperson và sales facts |
| `mart_sales` | Executive, monthly và country KPI |
| `mart_finance` | P&L gross-level |
| `mart_customer` | Customer base và RFM |
| `mart_product` | Product sales/profitability |
| `mart_sales_forecast` | Monthly series và EDA forecast |
| `analytics` | Feature, model output và metric |
| `audit` | Source-to-DW reconciliation và quality summary |

## Core DW

- `dim_date`
- `dim_customer`
- `dim_product`
- `dim_geography`
- `dim_salesperson`
- `fact_sales_order`
- `fact_sales_order_line`

## Analytics output

- `customer_segment` và customer model metrics.
- `product_association_rules`.
- `sales_forecast`, `sales_forecast_metric`, scenario và summary.

## Công cụ trình bày

- Superset TV1-TV3: EDA/KPI theo từng bài toán.
- Superset TV4: Executive KPI, gross-level P&L, reconciliation và quality.
- Streamlit: kết quả và recommendation của ba mô hình.
- MLflow: experiment/model metrics.
- dbt Docs: lineage và model documentation.
