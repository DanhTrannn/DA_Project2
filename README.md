# AdventureWorks OLTP Analytics

Đồ án sử dụng AdventureWorks OLTP trên PostgreSQL. Pipeline TV4 đã triển khai
import/staging, Core DW, DataMart nền, KPI quản trị, audit/reconciliation và
Macro Context. Các model Data Mining của TV1-TV3 sử dụng feature/mart do
pipeline này cung cấp.

## Phạm vi

Đã triển khai:

- AdventureWorks OLTP gồm 68 bảng thuộc các schema `sales`, `production`,
  `purchasing`, `person` và `humanresources`.
- 13 dbt staging views trong schema `staging` của database `Adventureworks`.
- Core DW: date/product/customer/geography dimensions và sales facts.
- DataMart nền cho Sales, Finance gross-level, Customer, Product và Forecast.
- Audit/reconciliation giữa OLTP và DW.
- Macro Context từ World Bank theo country/year.
- dbt data tests và Prefect flow end-to-end.
- Giao diện dbt Docs, Prefect, MLflow và Superset.

TV1 đã triển khai Customer Analytics với RFM + K-Means.
TV2 đã triển khai Product Analytics, FP-Growth, Streamlit Market Basket và
dashboard Superset Product Performance tập trung vào revenue concentration và
margin risk.
TV3 đã triển khai Sales Forecast Analytics trong ứng dụng Streamlit chung.

AdventureWorksDW vẫn là thành phần tùy chọn, không được dùng bởi pipeline chính.

AdventureWorks OLTP không có sổ cái tài chính và dữ liệu công nợ hoàn chỉnh.
KPI lợi nhuận, lỗ/lãi, nợ và tác động vĩ mô cần business rule hoặc nguồn dữ
liệu bổ sung trước khi triển khai.

## Khởi động

Không cần chạy script bên ngoài. Khởi động toàn bộ stack mặc định:

```bash
docker compose up -d --build
```

Chạy toàn bộ phần TV4 sau khi build:

```bash
./run_tv4.sh
```

Chạy mô hình TV1 và ứng dụng Streamlit chung:

```bash
./run_tv1.sh
```

Chạy mô hình TV3 và ứng dụng Streamlit chung:

```bash
./run_tv3.sh
```

Sau khi script hoàn tất, mở `http://localhost:8501`. Chạy lại script khi
DataMart có dữ liệu bán hàng mới để cập nhật forecast.

Xem nhanh các bảng kết quả TV3 bằng PostgreSQL:

```bash
docker compose exec -T db psql -U postgres -d Adventureworks < analytics/sql/tv3_check_output.sql
```

Khi Superset đang chạy, tạo/cập nhật các dashboard:

```bash
docker compose exec -T superset python /app/bootstrap/bootstrap_tv4.py
docker compose exec -T superset python /app/bootstrap/bootstrap_tv2.py
docker compose exec -T superset python /app/bootstrap/bootstrap_tv3.py
```

Khởi động một service và dependency của nó:

```bash
docker compose up -d db
docker compose up -d dbt
docker compose up -d dbt-docs
docker compose up -d prefect-server
docker compose up -d mlflow
docker compose up -d superset
```

Kiểm tra trạng thái:

```bash
docker compose ps
```

## Truy cập service

| Service | Truy cập |
|---|---|
| AdventureWorks OLTP PostgreSQL | `localhost:15432`, database `Adventureworks` |
| dbt Docs | `http://localhost:8081` |
| Prefect | `http://localhost:4200` |
| MLflow | `http://localhost:5000` |
| Superset | `http://localhost:8088`, tài khoản `admin` / `admin` |
| Superset TV2 | `http://localhost:8088/superset/dashboard/adventureworks-tv2-product-analytics/` |
| Superset TV3 | `http://localhost:8088/superset/dashboard/adventureworks-tv3-sales-forecast/` |
| Streamlit Analytics | `http://localhost:8501` |

Superset tự tạo kết nối OLTP:

```text
postgresql+psycopg2://postgres:postgres@db:5432/Adventureworks
```

## Thao tác trực tiếp

PostgreSQL:

```bash
docker compose exec db psql -U postgres -d Adventureworks
```

dbt:

```bash
docker compose exec dbt bash
dbt seed --project-dir /app/dbt --profiles-dir /app/dbt
dbt build --project-dir /app/dbt --profiles-dir /app/dbt
dbt ls --resource-type model
```

Prefect analytics flow:

```bash
docker compose exec prefect-server python -m orchestration.pipeline_flow
```

Vào shell các service:

```bash
docker compose exec db bash
docker compose exec dbt bash
docker compose exec prefect-server bash
docker compose exec mlflow bash
docker compose exec superset bash
```

Xem log và dừng stack:

```bash
docker compose logs -f dbt-docs
docker compose logs -f superset
docker compose stop
docker compose down
```

## dbt Analytics Pipeline

Lớp staging tạo các view sau:

- Sales: `stg_sales_order_header`, `stg_sales_order_detail`, `stg_customer`,
  `stg_store`, `stg_sales_territory`.
- Products: `stg_product`, `stg_product_subcategory`,
  `stg_product_category`.
- Purchasing: `stg_purchase_order_header`, `stg_purchase_order_detail`,
  `stg_vendor`.
- People và HR: `stg_person`, `stg_employee`.

Các schema TV4 được tạo thêm:

- `core_dw`: dimension/fact dùng chung.
- `mart_sales`: Executive, monthly và country-year KPI.
- `mart_finance`: P&L quản trị gross-level.
- `mart_customer`, `mart_product`, `mart_sales_forecast`: đầu vào cho TV1-TV3.
- `raw_macro`, `mart_macro`: World Bank observations và Macro Context.
- `analytics`: feature tables và macro correlation mô tả.
- `audit`: source-to-DW reconciliation và data-quality summary.

Tài liệu vận hành:

- `docs/PROJECT_STRUCTURE.md`
- `docs/TEAM_RUN_GUIDE.md`
- `docs/TV4_RUNBOOK.md`
- `docs/TV4_KPI_DICTIONARY.md`
- `docs/SUPERSET_TV4_DASHBOARD.md`
- `docs/SUPERSET_TV2_DASHBOARD.md`
- `docs/SUPERSET_TV3_DASHBOARD.md`

## AdventureWorksDW tùy chọn

DWH không được dùng bởi pipeline staging hiện tại. Chỉ khởi động khi cần tham
khảo:

```bash
docker compose --profile dw up -d dw
docker compose exec dw psql -U postgres -d AdventureworksDW
```
