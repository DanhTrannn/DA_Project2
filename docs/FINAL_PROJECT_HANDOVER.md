# Bàn giao đồ án AdventureWorks Analytics

## Kết quả đã xác nhận

| Hạng mục | Kết quả |
|---|---|
| Dữ liệu | 31.465 đơn, 121.317 dòng, 30/05/2022-29/06/2025 |
| Kho Dữ Liệu | staging, Core DW, DataMart, analytics và audit |
| dbt | 128/128 model và test PASS |
| Đối soát | 4 chỉ tiêu nguồn/DW khớp tuyệt đối |
| Data quality | 10/10 kiểm tra PASS |
| TV1 | 19.119 customer, K-Means, silhouette 0,4182 |
| TV2 | FP-Growth và association rules |
| TV3 | Linear Trend tốt nhất, WAPE 20,14% |
| Trực quan hóa | 4 dashboard Superset và 3 trang Streamlit; TV4 có 9 chart |

## KPI điều hành

| KPI | Giá trị |
|---|---:|
| Revenue | 109.846.381,40 |
| Estimated gross profit | 9.371.903,63 |
| Estimated gross margin | 8,53% |
| Loss amount | 5.034.387,64 |
| Order count | 31.465 |

## Insight TV4

1. Số đơn, số dòng và revenue trong DW khớp nguồn, tạo nền dữ liệu thống nhất
   cho ba bài phân tích.
2. Doanh nghiệp tạo 9,37 triệu gross profit ước tính nhưng có 5,03 triệu giá
   trị bán dưới giá vốn cần đi sâu ở Product Analytics.
3. Biên gross profit toàn kỳ là 8,53%; tăng doanh thu phải đi kèm kiểm soát
   product mix, giá bán và standard cost.
4. Data-quality checks giúp phân biệt insight thật với lỗi null, duplicate,
   date, quantity, price hoặc discount.

## Luồng demo

1. dbt Docs: nguồn -> staging -> Core DW -> DataMart.
2. TV4 Dashboard: Executive KPI -> P&L -> Reconciliation -> Data Quality.
3. TV1: Customer EDA -> K-Means -> recommendation.
4. TV2: Product EDA -> FP-Growth -> cross-sell.
5. TV3: Sales EDA -> model comparison -> forecast.
6. Kết luận: insight, hành động và giới hạn dữ liệu.

## URL

| Thành phần | URL |
|---|---|
| Streamlit | `http://localhost:8501` |
| Superset TV1 | `http://localhost:8088/superset/dashboard/tv1-customer-analytics/` |
| Superset TV2 | `http://localhost:8088/superset/dashboard/adventureworks-tv2-product-analytics/` |
| Superset TV3 | `http://localhost:8088/superset/dashboard/adventureworks-tv3-sales-forecast/` |
| Superset TV4 | `http://localhost:8088/superset/dashboard/adventureworks-tv4-executive-data-quality/` |
| MLflow | `http://localhost:5000` |
| dbt Docs | `http://localhost:8081` |
| Prefect | `http://localhost:4200` |

## Giới hạn phải nêu

- Không có net profit, debt, DSO/DPO hoặc cashflow thực.
- `estimated_cogs` dùng `standard_cost`.
- Tháng 06/2025 chưa hoàn chỉnh và bị loại khỏi huấn luyện forecast.
- TV2 phải chọn lọc rule có ý nghĩa thay vì trình bày toàn bộ.
