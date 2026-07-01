# Superset TV3 - Phân tích khám phá doanh thu

Dashboard TV3 chỉ trình bày EDA từ dữ liệu lịch sử: quy mô, xu hướng, hiệu quả,
thị trường, tăng trưởng YoY và mùa vụ. Kết quả mô hình forecast được tách riêng
sang Streamlit. Tiêu đề chart được tạo trực tiếp từ DataMart nên tự cập nhật
sau mỗi lần chạy pipeline.

## Nguồn dữ liệu

- `mart_sales_forecast.monthly_sales_eda`: chuỗi tháng hoàn chỉnh, revenue,
  gross profit, gross margin, YoY và thuộc tính mùa vụ.
- `mart_sales.sales_monthly_kpi`: doanh thu theo quốc gia và tháng.

Dashboard không đọc bảng `analytics.sales_forecast*`.

## Luồng dashboard

1. **Quy mô lịch sử:** tổng doanh thu, đơn hàng, sản lượng và gross margin.
2. **Xu hướng kinh doanh:** revenue, estimated gross profit và estimated gross
   margin theo tháng hoàn chỉnh.
3. **Phân rã và tăng trưởng:** doanh thu theo quốc gia và YoY theo tháng.
4. **Mùa vụ:** heatmap doanh thu theo tháng trong năm và năm dữ liệu.

## Đối chiếu file phân công TV3

| Yêu cầu Superset | Biểu đồ đáp ứng |
|---|---|
| Revenue trend theo tháng | Xu hướng doanh thu |
| Gross profit trend theo tháng | Lợi nhuận gộp theo tháng |
| Gross margin trend theo tháng | Biên lợi nhuận theo tháng |
| Revenue by territory/category | Doanh thu theo quốc gia |

WAPE theo model và actual-vs-forecast đã được loại khỏi Superset để tránh lặp
với Streamlit.

## Cách chạy

Sau khi dbt đã tạo `mart_sales_forecast.monthly_sales_eda`:

```bash
docker compose up -d --build superset
docker compose exec -T superset python /app/bootstrap/bootstrap_sales_dashboard.py
```

Hoặc chạy toàn bộ project:

```bash
./run_pipeline.sh
```

## Cách xem

1. Mở `http://localhost:8088`.
2. Đăng nhập bằng `admin` / `admin`, trừ khi đã đổi trong biến môi trường.
3. Chọn **Dashboards**.
4. Mở **Phân tích khám phá doanh thu AdventureWorks**.

Truy cập trực tiếp:

```text
http://localhost:8088/superset/dashboard/adventureworks-tv3-sales-forecast/
```

Streamlit là nơi trình bày model comparison, actual-vs-forecast, forecast
error, confidence interval, scenario và what-if:

```text
http://localhost:8501
```
