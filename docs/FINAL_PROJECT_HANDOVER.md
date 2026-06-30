# Bàn giao đồ án AdventureWorks Analytics

Tài liệu này chốt trạng thái có thể demo của đồ án sau khi chạy thành công
`./run_full_pipeline.sh` ngày 30/06/2026.

## 1. Kết quả kỹ thuật đã xác nhận

| Hạng mục | Kết quả |
|---|---|
| Dữ liệu bán hàng | 31.465 đơn, 121.317 dòng đơn, từ 30/05/2022 đến 29/06/2025 |
| Kho Dữ Liệu | staging, Core DW, DataMart, analytics và audit chạy được |
| dbt | 144/144 model, seed và test PASS |
| Đối soát | 4/4 chỉ tiêu nguồn và DW khớp tuyệt đối |
| Data quality | 11/11 kiểm tra PASS, 0 bản ghi lỗi |
| World Bank | 60 quan sát cho 6 quốc gia, giai đoạn 2022-2025 |
| Macro coverage | 18 country-year complete, 6 country-year partial ở năm 2025 |
| TV1 | 19.119 khách hàng được phân cụm, silhouette = 0,4182 |
| TV2 | 147.346 luật sau ngưỡng support/confidence/lift; dashboard chỉ trình bày phần đã chọn lọc |
| TV3 | Linear Trend tốt nhất trên tập test, WAPE = 20,14% |
| Trực quan hóa | Superset TV1/TV2/TV3/TV4 lần lượt có 6/11/10/13 chart; 3 trang Streamlit chạy được |

## 2. KPI điều hành

| KPI | Giá trị |
|---|---:|
| Revenue | 109.846.381,40 |
| Estimated gross profit | 9.371.903,63 |
| Estimated gross margin | 8,53% |
| Loss amount | 5.034.387,64 |
| Order count | 31.465 |

Các KPI lợi nhuận là **gross-level estimate** dựa trên `standard_cost`. Không
gọi đây là net profit vì AdventureWorks không có đủ chi phí hoạt động, công
nợ, thanh toán và dòng tiền.

## 3. Insight dùng trong phần trình bày TV4

1. Doanh thu nguồn và DW khớp 109.846.381,40; số đơn và số dòng cũng khớp,
   nên các phân tích phía sau dùng chung một nền KPI đáng tin cậy.
2. Doanh nghiệp tạo 9,37 triệu lợi nhuận gộp ước tính nhưng có 5,03 triệu
   giá trị lỗ ở các dòng bán dưới giá vốn. Đây là khu vực cần đi sâu bằng
   dashboard sản phẩm của TV2.
3. Biên lợi nhuận gộp toàn kỳ chỉ 8,53%; doanh thu lớn không đồng nghĩa hiệu
   quả tốt nếu cơ cấu sản phẩm hoặc giá bán làm lợi nhuận bị bào mòn.
4. Dữ liệu World Bank khớp giai đoạn AdventureWorks 2022-2025. Năm 2025 thiếu
   một phần CPI/GDP do dữ liệu công bố chưa đầy đủ, nên dashboard gắn trạng
   thái `partial_macro_data` thay vì tự điền hoặc mô phỏng.
5. Một số tương quan macro có độ lớn cao nhưng mỗi quốc gia chỉ có tối đa bốn
   năm quan sát. Chúng chỉ dùng để đặt câu hỏi và bổ sung bối cảnh, không đủ để
   kết luận CPI, GDP hay thất nghiệp gây ra biến động doanh thu.

## 4. Luồng demo với giảng viên

1. Mở dbt Docs để giới thiệu nguồn -> staging -> Core DW -> DataMart.
2. Mở dashboard TV4: KPI tổng quan -> P&L gross-level -> đối soát/chất lượng
   -> macro context.
3. Chuyển sang dashboard TV1 và Streamlit Customer để trình bày RFM + K-Means.
4. Chuyển sang dashboard TV2 và Streamlit Market Basket để trình bày EDA sản
   phẩm, luật mua kèm và đề xuất cross-sell.
5. Chuyển sang dashboard TV3 và Streamlit Forecast để trình bày xu hướng,
   baseline/model, WAPE và dự báo kỳ tới.
6. Quay lại kết luận: insight, hành động đề xuất, data gap và giới hạn mô hình.

## 5. Địa chỉ demo

| Thành phần | URL |
|---|---|
| Streamlit | `http://localhost:8501` |
| Superset TV1 | `http://localhost:8088/superset/dashboard/tv1-customer-analytics/` |
| Superset TV2 | `http://localhost:8088/superset/dashboard/adventureworks-tv2-product-analytics/` |
| Superset TV3 | `http://localhost:8088/superset/dashboard/adventureworks-tv3-sales-forecast/` |
| Superset TV4 | `http://localhost:8088/superset/dashboard/adventureworks-tv4-executive-macro/` |
| MLflow | `http://localhost:5000` |
| dbt Docs | `http://localhost:8081` |
| Prefect | `http://localhost:4200` |

Superset mặc định dùng tài khoản `admin`, mật khẩu `admin` nếu `.env` không
ghi đè.

## 6. Lệnh chạy và kiểm tra

```bash
./run_full_pipeline.sh
docker compose ps
```

Pipeline chỉ kết thúc thành công sau khi kiểm tra output ba model và chạy
AppTest cho cả ba trang Streamlit. Dashboard TV1 được import từ ZIP trong lúc
Superset khởi động; TV2, TV3 và TV4 được bootstrap idempotent ở bước 6.

## 7. Giới hạn phải nêu trong báo cáo

- Không có net profit, debt, DSO/DPO hay cashflow thực.
- `estimated_cogs` dùng `standard_cost`, không phải hệ thống kế toán đầy đủ.
- Tháng 06/2025 chưa hoàn chỉnh và bị loại khỏi tập huấn luyện forecast.
- TV2 có nhiều luật; chỉ chọn rule có ý nghĩa kinh doanh để trình bày.
- Macro có ít kỳ và năm 2025 chưa đủ chỉ số; không diễn giải theo hướng nhân quả.
