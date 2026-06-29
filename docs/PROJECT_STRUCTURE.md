# Project Structure - AdventureWorks Analytics

File này giải thích cấu trúc đồ án theo góc nhìn phân tích dữ liệu. Mục tiêu
không chỉ là biết file nằm ở đâu, mà là hiểu dữ liệu đi qua những lớp nào, mỗi
lớp phục vụ việc gì, và các thành viên tiếp theo cần gắn phần phân tích của
mình vào đâu.

## 1. Mục tiêu đồ án

Đồ án giải quyết bài toán doanh nghiệp bằng Kho Dữ Liệu trên bộ dữ liệu
AdventureWorks. Hướng triển khai chính:

- Nạp dữ liệu AdventureWorks vào PostgreSQL.
- Chuẩn hóa dữ liệu nguồn bằng dbt staging.
- Xây Core Data Warehouse gồm dimension và fact.
- Xây các DataMart phục vụ phân tích doanh nghiệp.
- Tính KPI doanh thu, lợi nhuận gộp ước tính, lỗ/lãi gross-level.
- Liên hệ KPI doanh nghiệp với dữ liệu vĩ mô từ World Bank.
- Cung cấp dữ liệu nền cho các mô hình Data Mining.
- Trình bày kết quả bằng Superset dashboard và báo cáo cuối.

## 2. Kiến trúc tổng quan

```text
AdventureWorks CSV / OLTP
        |
        v
PostgreSQL database: Adventureworks
        |
        v
dbt staging
        |
        v
Core DW: dimension + fact
        |
        v
DataMart: sales, finance, customer, product, forecast, macro
        |
        +--------------------+
        |                    |
        v                    v
Superset BI dashboard   Data Mining / analytics output
                             |
                             v
                         Report insight
```

Ý nghĩa của kiến trúc này: dữ liệu không được dùng trực tiếp từ OLTP cho báo
cáo cuối. OLTP chỉ là nguồn. Phần phân tích, dashboard và mô hình phải đọc từ
DW, DataMart hoặc bảng `analytics` đã chuẩn hóa.

## 3. Cấu trúc thư mục chính

| Đường dẫn | Vai trò |
|---|---|
| `data/` | CSV nguồn AdventureWorks dùng để import vào PostgreSQL |
| `install.sql` | Script tạo schema/bảng và import dữ liệu AdventureWorks |
| `docker-compose.yml` | Khởi động PostgreSQL, dbt, Superset, MLflow, Prefect |
| `analytics/dbt/` | Project dbt xây staging, Core DW, DataMart, tests |
| `analytics/dbt/models/staging/` | View chuẩn hóa từ OLTP |
| `analytics/dbt/models/core/` | Dimension/fact của Core DW |
| `analytics/dbt/models/marts/` | Các DataMart nghiệp vụ |
| `analytics/dbt/models/features/` | Feature table cho Data Mining và macro relation |
| `analytics/dbt/seeds/` | Dữ liệu seed, hiện có macro từ World Bank |
| `analytics/dbt/scripts/` | Script tải dữ liệu macro chính thức |
| `analytics/src/aw_analytics/` | Code Python cho Data Mining/analytics |
| `analytics/streamlit/Home.py` | Entry point của ứng dụng Streamlit chung |
| `analytics/streamlit/pages/` | Các trang model của TV1, TV2, TV3 |
| `analytics/sql/` | Truy vấn kiểm tra output analytics |
| `analytics/orchestration/` | Flow orchestration cho pipeline |
| `superset/` | Config và bootstrap dashboard Superset |
| `docs/` | Tài liệu vận hành, KPI, dashboard và cấu trúc đồ án |
| `run_tv4.sh` | Script chạy pipeline nền TV4 end-to-end |
| `run_tv3.sh` | Chạy model TV3 và khởi động app Streamlit chung |

## 4. Các lớp dữ liệu trong PostgreSQL

### 4.1 OLTP source

Database `Adventureworks` chứa dữ liệu nguồn được import từ CSV. Các schema
nguồn chính:

- `sales`
- `production`
- `purchasing`
- `person`
- `humanresources`

Lớp này chỉ dùng làm input cho dbt. Không nên dùng trực tiếp để vẽ dashboard
hoặc chạy mô hình cuối kỳ, vì mỗi người tự join OLTP sẽ dễ lệch công thức KPI.

### 4.2 Staging

Schema: `staging`

Vai trò:

- Chuẩn hóa tên cột.
- Ép kiểu dữ liệu.
- Giữ grain gần với bảng nguồn.
- Làm lớp trung gian để Core DW không phụ thuộc trực tiếp vào bảng OLTP.

Ví dụ model:

- `stg_sales_order_header`
- `stg_sales_order_detail`
- `stg_customer`
- `stg_product`
- `stg_sales_territory`

### 4.3 Core Data Warehouse

Schema: `core_dw`

Vai trò:

- Tạo dimension và fact dùng chung.
- Chuẩn hóa khóa phân tích.
- Đảm bảo mọi DataMart tính KPI từ cùng một nền dữ liệu.

Bảng chính:

| Bảng | Vai trò |
|---|---|
| `dim_date` | Dimension thời gian |
| `dim_customer` | Dimension khách hàng |
| `dim_product` | Dimension sản phẩm |
| `dim_geography` | Dimension địa lý/country/territory |
| `fact_sales_order` | Fact cấp đơn hàng |
| `fact_sales_order_line` | Fact cấp dòng đơn hàng |

Core DW là phần quan trọng nhất để các thành viên gộp bài được. TV1, TV2, TV3
nên lấy dữ liệu từ đây hoặc từ DataMart được xây trên đây.

### 4.4 DataMart

DataMart là lớp phục vụ câu hỏi phân tích cụ thể. Mỗi mart đã được tính sẵn
theo grain phù hợp, giúp giảm việc join và tránh lệch KPI.

| Schema | Mục đích |
|---|---|
| `mart_sales` | Doanh thu, số đơn, số lượng bán, KPI theo tháng/quốc gia |
| `mart_finance` | P&L gross-level, estimated COGS, gross profit, loss amount |
| `mart_customer` | Customer base, RFM, customer value |
| `mart_product` | Tổng hợp doanh thu/lợi nhuận theo sản phẩm |
| `mart_sales_forecast` | Chuỗi thời gian doanh thu tháng cho forecasting |
| `mart_macro` | KPI doanh nghiệp kết hợp CPI, GDP growth, unemployment |

Các mart nền này là điểm bắt đầu cho phân tích của TV1, TV2, TV3.

### 4.5 Analytics

Schema: `analytics`

Vai trò:

- Chứa feature table cho mô hình Data Mining.
- Chứa output mô tả/correlation phục vụ báo cáo.
- Là nơi hợp lý để lưu kết quả cuối của các mô hình sau này.

Bảng hiện có:

- `feature_customer_rfm`
- `feature_monthly_sales`
- `macro_kpi_relation`

Khi TV1, TV2, TV3 làm xong model, nên đưa output vào schema này, ví dụ:

- `customer_segments`
- `market_basket_rules`
- `sales_forecast_result`
- `model_evaluation_metrics`

### 4.6 Audit

Schema: `audit`

Vai trò:

- Kiểm tra dữ liệu nguồn và DW có khớp nhau không.
- Ghi nhận data quality.
- Là bằng chứng trong báo cáo rằng kho dữ liệu được kiểm thử.

Bảng chính:

- `source_to_dw_reconciliation`
- `data_quality_summary`

## 5. Macro data

Dữ liệu vĩ mô được lấy từ World Bank Indicators API, lưu ở seed:

`analytics/dbt/seeds/macro_observations.csv`

Các chỉ số đang dùng:

| Indicator | Ý nghĩa |
|---|---|
| `FP.CPI.TOTL.ZG` | Inflation, consumer prices, annual % |
| `NY.GDP.MKTP.KD.ZG` | GDP growth, annual % |
| `SL.UEM.TOTL.ZS` | Unemployment, total, % of labor force |

Luồng macro:

```text
World Bank API
    |
    v
raw_macro.macro_observations
    |
    v
mart_macro.macro_observation_standardized
    |
    v
mart_macro.business_kpi_macro_period
    |
    v
analytics.macro_kpi_relation
```

Phần macro chỉ dùng để tạo bối cảnh phân tích. Không kết luận CPI, GDP hay
thất nghiệp là nguyên nhân trực tiếp làm doanh thu thay đổi.

## 6. Dashboard và công cụ trình bày

Superset dùng để trình bày BI dashboard từ DataMart. Dashboard hiện tại:

`http://localhost:8088/superset/dashboard/adventureworks-tv4-executive-macro/`

Các nhóm chart nên có trong đồ án cuối:

- Executive KPI: doanh thu, gross profit, margin.
- Sales trend: doanh thu theo thời gian/quốc gia.
- Customer insight: nhóm khách hàng, RFM, segment.
- Product insight: sản phẩm bán tốt, sản phẩm lỗ, basket rules.
- Forecast: doanh thu thực tế và dự báo.
- Macro context: KPI doanh nghiệp đặt cạnh CPI, GDP growth, unemployment.
- Audit: reconciliation và data quality.

## 7. Vai trò các thành viên trong cấu trúc này

| Thành viên | Phần chính | Nguồn dữ liệu nên dùng | Output cần trả về |
|---|---|---|---|
| TV1 | Customer analysis + segmentation | `mart_customer`, `analytics.feature_customer_rfm` | Segment, profile từng nhóm, insight khách hàng |
| TV2 | Product analysis + market basket | `core_dw.fact_sales_order_line`, `mart_product` | Association rules, sản phẩm đi kèm, insight sản phẩm |
| TV3 | Sales trend + forecasting | `mart_sales`, `mart_sales_forecast` | Forecast result, model metrics, insight xu hướng |
| TV4 | DW foundation + BI integration + macro | Toàn bộ DW/mart/analytics/audit | Dashboard tổng hợp, macro relation, runbook, báo cáo tích hợp |

TV4 làm phần nền trước. Sau đó TV1, TV2, TV3 có thể làm song song trên các mart
đã có. Khi các model xong, TV4 gộp output vào dashboard và báo cáo cuối.

## 8. Flow làm việc đề xuất

1. Chạy `./run_tv4.sh` để dựng nền dữ liệu.
2. Kiểm tra `audit.source_to_dw_reconciliation` và `audit.data_quality_summary`.
3. TV1, TV2, TV3 lấy dữ liệu từ mart/analytics đúng phần của mình.
4. Mỗi thành viên lưu output model về schema `analytics`.
5. Mỗi model có một page trong cùng ứng dụng `analytics/streamlit/`.
6. TV4 cập nhật Superset dashboard và báo cáo tổng hợp.
7. Chạy lại dbt/audit để đảm bảo dữ liệu không vỡ.
8. Demo theo luồng: nguồn dữ liệu, DW, mart, model, dashboard, insight.

## 9. Giới hạn cần nói rõ trong báo cáo

- AdventureWorks không có đầy đủ sổ cái kế toán, khoản vay, lịch thanh toán và
  chi phí vận hành.
- `mart_finance` chỉ là P&L gross-level, không phải báo cáo lợi nhuận ròng.
- Estimated COGS dùng `Product.StandardCost`, nên gross profit là ước tính.
- Macro data có grain theo năm/quốc gia, nên chỉ phù hợp làm bối cảnh mô tả.
- Tương quan macro không chứng minh quan hệ nhân quả.

## 10. Tóm tắt cấu trúc

Project hiện tại đã có nền DW đủ để các thành viên tiếp tục phân tích:

- PostgreSQL chứa nguồn AdventureWorks.
- dbt tạo staging, Core DW và DataMart.
- DataMart cung cấp dữ liệu chuẩn cho phân tích và dashboard.
- `analytics` là nơi đặt feature/output Data Mining.
- `audit` kiểm tra độ tin cậy dữ liệu.
- Superset trình bày KPI và insight cuối.

Phần còn lại của nhóm là hoàn thiện model TV1-TV3, đưa kết quả vào cùng cấu
trúc này, rồi TV4 gộp dashboard và báo cáo.
