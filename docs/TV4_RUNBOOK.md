# TV4 Runbook - Data Platform, BI Integration and Macro Context

## 1. Chạy pipeline

```bash
./run_tv4.sh
```

Script thực hiện theo thứ tự:

1. Khởi động PostgreSQL và dbt.
2. Thử tải dữ liệu vĩ mô từ World Bank Indicators API.
3. Nạp macro CSV bằng `dbt seed` vào schema `raw_macro`.
4. Chạy staging, Core DW, DataMart, analytics và audit tests.

Nếu chỉ cần chạy lại dbt mà không tải macro:

```bash
docker compose exec -T dbt dbt seed --project-dir /app/dbt --profiles-dir /app/dbt
docker compose exec -T dbt dbt build --project-dir /app/dbt --profiles-dir /app/dbt
```

## 2. Kiểm tra kết quả

```bash
docker compose exec -T db psql -U postgres -d Adventureworks -P pager=off -c \
  "select * from audit.source_to_dw_reconciliation order by metric_name;"

docker compose exec -T db psql -U postgres -d Adventureworks -P pager=off -c \
  "select * from mart_sales.executive_kpi;"

docker compose exec -T db psql -U postgres -d Adventureworks -P pager=off -c \
  "select * from mart_macro.business_kpi_macro_period order by country_code, year;"
```

Pipeline đạt yêu cầu khi:

- Các dòng trong `audit.source_to_dw_reconciliation` đều có `status = 'PASS'`.
- `audit.data_quality_summary` không có `status = 'FAIL'`.
- `mart_sales.executive_kpi` có một dòng KPI tổng quan.
- Macro Context có `macro_coverage_status = 'complete'` sau khi tải World Bank thành công.

Nếu World Bank timeout, pipeline vẫn chạy. `macro_coverage_status` sẽ là
`missing_macro_data` và `audit.data_quality_summary` ghi `WARN`; không có số
liệu vĩ mô giả được chèn vào kết quả.

## 3. Schema được tạo

| Schema | Nội dung |
|---|---|
| `staging` | View chuẩn hóa từ OLTP |
| `core_dw` | Dimension và fact bán hàng |
| `mart_sales` | Executive/monthly/country-year sales KPI |
| `mart_finance` | P&L quản trị gross-level |
| `mart_customer` | Customer base và RFM |
| `mart_product` | Product profitability summary |
| `mart_sales_forecast` | Monthly time series cho TV3 |
| `raw_macro` | World Bank observations |
| `mart_macro` | Business KPI kết hợp macro theo country-year |
| `analytics` | Feature tables và macro correlation mô tả |
| `audit` | Reconciliation và data quality summary |

## 4. Làm mới dữ liệu vĩ mô

```bash
docker compose exec -T \
  dbt python /app/dbt/scripts/load_world_bank_macro.py
```

Loader tự đọc năm nhỏ nhất/lớn nhất từ `sales.salesorderheader`. Có thể đặt
`MACRO_START_YEAR` và `MACRO_END_YEAR` khi cần ghi đè.

Các quốc gia mặc định khớp với `SalesTerritory.CountryRegionCode`: US, CA,
GB, FR, DE, AU.

Các indicator mặc định:

- `FP.CPI.TOTL.ZG`: inflation, consumer prices, annual %.
- `NY.GDP.MKTP.KD.ZG`: GDP growth, annual %.
- `SL.UEM.TOTL.ZS`: unemployment, total, % of labor force.

Nguồn: World Bank Indicators API. API không yêu cầu khóa truy cập. Seed lưu cả
`source_url` và `retrieved_at` để truy vết.

## 5. Giới hạn phân tích

- COGS dùng `Product.StandardCost`, do đó gross profit là ước tính quản trị.
- AdventureWorks không có sổ cái, khoản vay hoặc lịch thanh toán đầy đủ; không
  trình bày net profit, debt, DSO/DPO hoặc cashflow như số liệu thật.
- Macro Context chỉ thể hiện bối cảnh/tương quan mô tả. Không dùng correlation
  để kết luận CPI, GDP hoặc thất nghiệp gây ra thay đổi doanh thu.
- Mỗi quốc gia chỉ có vài năm dữ liệu AdventureWorks; luôn trình bày sample size.
