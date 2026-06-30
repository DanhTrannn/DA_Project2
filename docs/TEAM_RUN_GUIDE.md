# Team Run Guide

Tài liệu này dùng cho cả nhóm. Mục tiêu là chạy được project theo cùng một
luồng, dùng chung một kho dữ liệu, rồi để từng thành viên chỉ tập trung vào
phần phân tích và mô hình của mình.

## 1. Chạy toàn bộ project

Từ thư mục gốc `AdventureWorks-for-Postgres`:

```bash
./run_full_pipeline.sh
```

Script sẽ:

1. Khởi động PostgreSQL và dbt.
2. Tải lại macro chính thức từ World Bank.
3. Nạp seed macro vào `raw_macro`.
4. Chạy staging, Core DW, DataMart, analytics và audit tests.
5. Chạy ba mô hình Data Mining và kiểm tra output.
6. Tạo bốn dashboard Superset.
7. Khởi động và kiểm tra Streamlit, MLflow, dbt Docs và Prefect.

Nếu chỉ cần chạy lại phần nền của TV4, dùng `./run_tv4.sh`.

## 2. Kiểm tra kết quả

```bash
docker compose exec -T db psql -U postgres -d Adventureworks -P pager=off -c \
  "select * from audit.source_to_dw_reconciliation order by metric_name;"

docker compose exec -T db psql -U postgres -d Adventureworks -P pager=off -c \
  "select * from audit.data_quality_summary order by check_name;"

docker compose exec -T db psql -U postgres -d Adventureworks -P pager=off -c \
  "select * from mart_sales.executive_kpi;"

docker compose exec -T db psql -U postgres -d Adventureworks -P pager=off -c \
  "select * from mart_macro.business_kpi_macro_period order by country_code, year;"
```

Kết quả mong đợi:

- Reconciliation `PASS`.
- Data quality không có `FAIL`.
- `mart_sales.executive_kpi` có số tổng quan doanh nghiệp.
- `mart_macro.business_kpi_macro_period` có dữ liệu macro theo `country/year`.

## 3. Kiến trúc DW cần giữ cho các thành viên sau

Các thành viên sau không nên tự dựng lại nguồn hay tự tính lại cùng một logic.
Họ nên bám vào các lớp đã có:

| Lớp | Vai trò |
|---|---|
| `staging` | Chuẩn hóa OLTP sang kiểu dữ liệu, tên cột và grain thống nhất |
| `core_dw` | Dimension/fact dùng chung để mọi mart lấy dữ liệu |
| `mart_sales` | KPI bán hàng và KPI quản trị tổng quan |
| `mart_finance` | P&L gross-level để trình bày lợi nhuận gộp và lỗ |
| `mart_customer` | Customer base, RFM và đầu vào cho phân khúc khách hàng |
| `mart_product` | Tổng hợp theo sản phẩm, phục vụ phân tích giỏ hàng và profit |
| `mart_sales_forecast` | Chuỗi thời gian doanh thu cho dự báo |
| `raw_macro` | Dữ liệu World Bank gốc |
| `mart_macro` | Join KPI doanh nghiệp với macro theo `country/year` |
| `analytics` | Feature tables và output của data mining |
| `audit` | Reconciliation và data quality để chứng minh DW đúng |

## 4. Phần DW tối thiểu các thành viên sau cần dùng

### Thành viên làm customer segmentation

Cần:

- `core_dw.dim_customer`
- `mart_customer.customer_base`
- `mart_customer.customer_rfm`
- `analytics.feature_customer_rfm`

### Thành viên làm market basket / product mining

Cần:

- `core_dw.fact_sales_order_line`
- `core_dw.dim_product`
- `mart_product.product_sales_summary`

### Thành viên làm forecasting / trend analysis

Cần:

- `mart_sales.sales_monthly_kpi`
- `mart_sales_forecast.monthly_sales_series`
- `analytics.feature_monthly_sales`

### Thành viên làm macro relation / BI tổng hợp

Cần:

- `mart_sales.sales_country_year_kpi`
- `mart_macro.business_kpi_macro_period`
- `analytics.macro_kpi_relation`
- `audit.source_to_dw_reconciliation`

## 5. Nếu chỉ cần chạy lại dbt

```bash
docker compose exec -T dbt dbt seed --project-dir /app/dbt --profiles-dir /app/dbt
docker compose exec -T dbt dbt build --project-dir /app/dbt --profiles-dir /app/dbt
```

## 6. Nếu muốn mở Superset

```bash
curl -fsS http://localhost:8088/health
```

Nếu Superset đang chạy, dashboard TV4 đã được bootstrap tại:

`http://localhost:8088/superset/dashboard/adventureworks-tv4-executive-macro/`

## 7. Ghi chú quan trọng

- Không đọc trực tiếp từ OLTP để làm báo cáo cuối.
- KPI tài chính ở đây là gross-level, không phải báo cáo kế toán đầy đủ.
- Macro chỉ là bối cảnh mô tả, không kết luận quan hệ nhân quả.
- Khi gộp bài của các thành viên, luôn giữ chung khóa `customer`, `product`,
  `order`, `country`, `year`.
