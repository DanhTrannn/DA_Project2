# Team Run Guide

## Chạy toàn bộ đồ án

```bash
./run_full_pipeline.sh
```

Pipeline thực hiện:

1. Khởi động PostgreSQL, dbt, MLflow và Superset.
2. Xây staging, Core DW, DataMart, analytics features và audit.
3. Chạy TV1 Customer Segmentation, TV2 Market Basket và TV3 Forecast.
4. Kiểm tra số dòng output của ba model.
5. Bootstrap bốn dashboard Superset.
6. Khởi động và kiểm tra Streamlit, dbt Docs và Prefect.
7. Chạy AppTest cho cả ba trang Streamlit.

Chỉ chạy nền TV4:

```bash
./run_tv4.sh
```

## Kiểm tra dữ liệu

```bash
docker compose exec -T db psql -U postgres -d Adventureworks -P pager=off -c \
  "select * from audit.source_to_dw_reconciliation order by metric_name;"

docker compose exec -T db psql -U postgres -d Adventureworks -P pager=off -c \
  "select * from audit.data_quality_summary order by check_name;"

docker compose exec -T db psql -U postgres -d Adventureworks -P pager=off -c \
  "select * from mart_sales.executive_kpi;"
```

Kết quả đạt yêu cầu khi reconciliation và data quality không có `FAIL`.

## Nguồn dữ liệu theo thành viên

| Thành viên | Bảng đầu vào chính | Output chính |
|---|---|---|
| TV1 | `mart_customer.customer_rfm` | `analytics.customer_segment` |
| TV2 | `core_dw.fact_sales_order_line`, `mart_product.product_sales_summary` | `analytics.product_association_rules` |
| TV3 | `mart_sales_forecast.monthly_sales_series` | `analytics.sales_forecast` |
| TV4 | toàn bộ DW/mart/audit | dashboard Executive & Data Quality |

## Truy cập

| Thành phần | URL |
|---|---|
| Streamlit | `http://localhost:8501` |
| Superset | `http://localhost:8088` |
| TV4 | `http://localhost:8088/superset/dashboard/adventureworks-tv4-executive-data-quality/` |
| MLflow | `http://localhost:5000` |
| dbt Docs | `http://localhost:8081` |
| Prefect | `http://localhost:4200` |

Không đọc trực tiếp OLTP cho báo cáo cuối. KPI tài chính chỉ phản ánh
gross-level vì nguồn không có sổ cái và dữ liệu thanh toán đầy đủ.
