# Phân công đồ án Phân tích dữ liệu cho 4 thành viên

## 1. Kiến trúc và nguyên tắc chung

```text
AdventureWorks -> PostgreSQL -> dbt DW/DataMart
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
             Superset EDA/KPI          Analytics model output
                                                |
                                                v
                                           Streamlit
```

- TV1, TV2, TV3 mỗi người phụ trách một bài phân tích và một mô hình.
- TV4 phụ trách nền dữ liệu, KPI, kiểm chứng và tích hợp dashboard.
- Superset trình bày EDA/KPI từ mart; Streamlit trình bày kết quả model.
- Mỗi người phải có business question, metric, insight và recommendation.

## 2. Phân công tổng quan

| Thành viên | Phần phân tích | Data Mining/Platform | Đầu ra chính |
|---|---|---|---|
| TV1 | Giá trị và hành vi khách hàng | RFM + K-Means | Customer mart, segment, dashboard/app |
| TV2 | Hiệu quả sản phẩm và mua kèm | FP-Growth | Product mart, association rules, dashboard/app |
| TV3 | Xu hướng, mùa vụ và dự báo | Time-series models | Forecast mart/output, dashboard/app |
| TV4 | Executive, P&L và chất lượng dữ liệu | DW, dbt, BI integration | Core DW, audit, dashboard TV4, tài liệu |

## 3. TV1 - Customer Analytics

### Câu hỏi phải trả lời

1. Khách hàng nào đóng góp nhiều revenue và gross profit?
2. Khách hàng nào mua thường xuyên hoặc đã lâu không quay lại?
3. Các nhóm khách hàng khác nhau như thế nào?
4. Nên giữ chân, upsell hoặc tái kích hoạt nhóm nào?

### Cách làm

1. Kiểm tra và mô tả phân phối Recency, Frequency, Monetary, AOV.
2. Xử lý lệch phân phối bằng `log1p`, sau đó StandardScaler.
3. Chạy K-Means với `k = 3..6`.
4. So sánh silhouette và inertia; chọn số cụm có thể diễn giải.
5. Đặt tên segment theo profile, không đặt tên tùy ý.
6. Lưu segment, profile, EDA và model metric vào `analytics`.

### Visualization

- Superset: top customer revenue/profit, customer value theo territory, RFM.
- Streamlit: segment distribution, revenue/profit theo segment, scatter
  Frequency-Monetary, High Value, At Risk, model evaluation.

### Kết quả bắt buộc

- `analytics.customer_segment` có dữ liệu.
- Có silhouette score và so sánh nhiều giá trị `k`.
- Có ít nhất ba insight và recommendation theo segment.
- Giải thích được công thức RFM và cách chọn cụm.

## 4. TV2 - Product & Cross-sell Analytics

### Câu hỏi phải trả lời

1. Category/product nào dẫn đầu revenue, quantity và gross profit?
2. Sản phẩm nào có margin thấp hoặc bán dưới giá vốn?
3. Sản phẩm nào thường xuất hiện cùng một đơn hàng?
4. Combo/cross-sell nào đủ support, confidence và lift?

### Cách làm

1. EDA product/category từ `mart_product.product_sales_summary`.
2. Tạo basket với một order là một transaction.
3. One-hot encode tập sản phẩm và chạy FP-Growth.
4. Sinh association rules và lọc theo ngưỡng chất lượng.
5. Chọn top rule có ý nghĩa; không trình bày toàn bộ tập luật.
6. Lưu output vào `analytics.product_association_rules`.

### Visualization

- Superset: category revenue/margin, top product, loss-making product,
  profitability matrix.
- Streamlit: rule table/filter, top lift, network và recommendation theo
  sản phẩm được chọn.

### Kết quả bắt buộc

- Có transaction basket sạch và output rule.
- Mỗi rule có support, confidence và lift.
- Có ít nhất 10 rule đạt ngưỡng, sau đó chọn lọc rule để báo cáo.
- Có ít nhất ba insight và đề xuất bundle/cross-sell.

## 5. TV3 - Sales Forecast Analytics

### Câu hỏi phải trả lời

1. Revenue, gross profit và margin biến động theo thời gian ra sao?
2. Có xu hướng hoặc mùa vụ nào đáng chú ý?
3. Model nào tốt hơn baseline trên tập test?
4. Revenue kỳ tiếp theo và mức rủi ro dự báo là gì?

### Cách làm

1. EDA chuỗi tháng và loại tháng chưa hoàn chỉnh.
2. Tính MoM/YoY; chỉ hiển thị YoY khi có kỳ cùng tháng năm trước.
3. Chia train/test theo thời gian.
4. Chạy Seasonal Naive, Moving Average, Linear Trend, Holt-Winters, SARIMA.
5. So sánh MAE, RMSE, MAPE và WAPE.
6. Lưu forecast, metric, decomposition, scenario và summary vào `analytics`.

### Visualization

- Superset: revenue/gross profit/margin trend, territory, YoY và seasonality.
- Streamlit: model ranking, actual vs forecast, forecast error, scenario,
  decomposition và recommendation.

### Kết quả bắt buộc

- Có baseline và ít nhất một model chính.
- Có model metric và forecast output.
- Có ít nhất ba insight về xu hướng, mùa vụ và kỳ tiếp theo.
- Giải thích được vì sao không shuffle time series.

## 6. TV4 - Data Platform, Executive BI và Data Quality

### Câu hỏi phải trả lời

1. Dữ liệu nguồn đã được import và chuẩn hóa đầy đủ chưa?
2. Revenue, số đơn và số dòng trong DW có khớp nguồn không?
3. KPI điều hành và P&L gross-level cho thấy điều gì?
4. Dữ liệu có null, duplicate hoặc giá trị bất hợp lệ không?
5. Làm sao kết nối phần EDA và model của ba thành viên thành một luồng demo?

### Cách làm

1. Duy trì Docker/PostgreSQL và quy trình import AdventureWorks.
2. Xây staging và Core DW:
   - `dim_date`, `dim_customer`, `dim_product`.
   - `dim_geography`, `dim_salesperson`.
   - `fact_sales_order`, `fact_sales_order_line`.
3. Xây mart nền cho sales, finance, customer, product và forecast.
4. Chuẩn hóa KPI dictionary và gross-level accounting caveat.
5. Xây reconciliation:
   - source/DW order count.
   - source/DW line count.
   - source/DW revenue.
   - header subtotal/detail revenue.
6. Xây data-quality checks cho key, duplicate, date, quantity, price,
   discount và revenue.
7. Bootstrap dashboard TV1-TV4 theo cách idempotent, không tạo chart trùng.
8. Duy trì full pipeline và tài liệu bàn giao.

### Visualization

Dashboard TV4 gồm:

1. Revenue, gross profit, gross margin, order count và loss amount.
2. Revenue/gross-profit trend.
3. P&L gross-level: revenue, estimated COGS, gross profit, loss amount.
4. Source-to-DW reconciliation table.
5. Data-quality status table.

### Kết quả bắt buộc

- dbt build và tests PASS.
- Reconciliation không có FAIL.
- Data quality không có FAIL.
- Dashboard TV4 chạy được và đọc từ mart/audit.
- `run_pipeline.sh` chạy được end-to-end.
- Có README, run guide, KPI dictionary, project structure và handover.

## 7. Công việc chung

| Công việc | Người chính | Người kiểm tra |
|---|---|---|
| Chốt KPI và grain | TV4 | TV1-TV3 theo phần mình |
| Customer feature/model | TV1 | TV4 kiểm tra contract |
| Product basket/model | TV2 | TV4 kiểm tra output |
| Sales series/model | TV3 | TV4 kiểm tra output |
| Superset chart từng phần | TV1-TV3 | TV4 tích hợp |
| Streamlit model pages | TV1-TV3 | TV4 chạy AppTest |
| Data quality/reconciliation | TV4 | Cả nhóm đọc kết quả |
| Báo cáo cuối | Cả nhóm | TV4 thống nhất cấu trúc |

## 8. Definition of Done

Đồ án hoàn thành khi:

1. PostgreSQL và toàn bộ service cần thiết chạy được.
2. Staging, Core DW, DataMart, analytics và audit tồn tại.
3. dbt tests và reconciliation PASS.
4. Ba model có output và metric đánh giá.
5. Bốn dashboard Superset và ba trang Streamlit hoạt động.
6. Mỗi thành viên có ít nhất ba insight và action tương ứng.
7. Báo cáo nêu đúng giới hạn về net profit, debt và cashflow.

## 9. Flow báo cáo

1. TV4 mở đầu: bài toán, kiến trúc, KPI, chất lượng và đối soát.
2. TV1: Customer EDA -> RFM -> K-Means -> recommendation.
3. TV2: Product EDA -> FP-Growth -> cross-sell.
4. TV3: Sales EDA -> model comparison -> forecast.
5. TV4 kết luận: Executive/P&L dashboard, insight chung và data gap.
