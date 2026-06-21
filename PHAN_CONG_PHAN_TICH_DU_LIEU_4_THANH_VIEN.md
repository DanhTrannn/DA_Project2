# Phân công theo hướng 3 mô hình Data Mining + 1 Data Platform/BI - Nhóm 4 thành viên

Tài liệu này chia công việc theo hướng gọn và dễ báo cáo: **3 thành viên đầu mỗi người phụ trách một phần phân tích dữ liệu và một mô hình Data Mining riêng**; **thành viên 4 phụ trách import dữ liệu, Kho Dữ Liệu, dashboard tổng hợp và phần liên hệ kinh tế vĩ mô**.

Mục tiêu là mỗi thành viên đều có phần trình bày rõ:

1. Phần phân tích dữ liệu cần làm.
2. Dữ liệu/KPI sử dụng.
3. Mô hình Data Mining áp dụng, nếu có.
4. Biểu đồ/dashboard/app thể hiện kết quả.
5. Insight và khuyến nghị kinh doanh.

## 1. Phạm vi đã chốt

- Dữ liệu chính: AdventureWorks.
- Database: PostgreSQL.
- Kho dữ liệu: staging, Core DW, DataMart, analytics, audit.
- BI dashboard: Superset.
- Data Mining visualization: Streamlit.
- 3 bài toán Data Mining chính:
  - Customer Segmentation bằng RFM + K-Means.
  - Product Cross-sell/Market Basket bằng Apriori hoặc FP-Growth.
  - Sales Forecast bằng Seasonal Naive/Holt-Winters/ARIMA.
- Thành viên 4 làm thêm phần liên hệ kinh tế vĩ mô ở mức **macro-lite**:
  - GDP growth.
  - inflation.
  - unemployment.
  - exchange rate nếu dữ liệu phù hợp.
- Phân tích vĩ mô chỉ dùng để bổ sung bối cảnh/tương quan mô tả, không kết luận nhân quả.
- Không mô phỏng nợ, cashflow, DSO/DPO, net profit thật vì AdventureWorks thiếu dữ liệu kế toán/thanh toán.

## 2. Kiến trúc đề xuất

```text
AdventureWorks OLTP + dữ liệu vĩ mô gọn
        |
        v
PostgreSQL Raw/Staging
        |
        v
Core Data Warehouse
        |
        v
DataMart nghiệp vụ
        |
        +--------------------------+
        |                          |
        v                          v
Superset BI Dashboard        Analytics Tables
                                   |
                                   v
                            Streamlit Mining App
                                   |
                                   v
                    Insight + Recommendation + Báo cáo
```

| Lớp | Mục đích | Người chính |
|---|---|---|
| Raw/Staging | Import và chuẩn hóa dữ liệu nguồn | TV4 |
| Core DW | Dimension/fact dùng chung cho cả nhóm | TV4 |
| DataMart | Bảng KPI phục vụ phân tích và dashboard | TV1/TV2/TV3 tạo yêu cầu, TV4 hỗ trợ chuẩn hóa |
| Analytics | Bảng lưu feature/model output | TV1/TV2/TV3 chính, TV4 hỗ trợ schema |
| Superset | Dashboard KPI quản trị từ DataMart | TV4 tổng hợp, TV1/TV2/TV3 đóng góp chart |
| Streamlit | App trình bày kết quả Data Mining | TV1/TV2/TV3 làm page model, TV4 hỗ trợ kết nối |
| Báo cáo | Giải thích phương pháp, insight, data gap, khuyến nghị | Cả nhóm |

## 3. Phân công tổng quan

| Thành viên | Vai trò | Phần phân tích dữ liệu | Mô hình Data Mining áp dụng | Đầu ra chính |
|---|---|---|---|---|
| TV1 | Customer Analytics | Phân tích giá trị khách hàng, RFM, nhóm khách hàng và hành vi mua | K-Means clustering | `mart_customer`, `analytics.customer_segment`, Streamlit Customer page |
| TV2 | Product & Cross-sell Analytics | Phân tích sản phẩm bán chạy, sản phẩm mua kèm, combo/cross-sell | Apriori hoặc FP-Growth | `mart_product`, `analytics.product_association_rule`, Streamlit Market Basket page |
| TV3 | Sales Forecast Analytics | Phân tích xu hướng doanh thu, mùa vụ, tăng trưởng và dự báo doanh thu | Seasonal Naive + Holt-Winters/ARIMA | `mart_sales_forecast`, `analytics.sales_forecast`, Streamlit Forecast page |
| TV4 | Data Platform + BI Integration + Executive/Macro Analytics | Import data, Core DW, KPI tổng quan, data quality, reconciliation, dashboard, liên hệ kinh tế vĩ mô | Không bắt buộc model riêng | PostgreSQL/DW chạy được, Superset dashboard, KPI dictionary, audit/reconciliation, `mart_macro` |

Nguyên tắc chia việc:

1. TV1/TV2/TV3 mỗi người có một bài phân tích và một mô hình Data Mining rõ ràng.
2. TV4 không bắt buộc có model, nhưng có phần phân tích dữ liệu riêng: Executive KPI, Data Quality, Reconciliation và Macro Context.
3. Superset dùng để trình bày KPI/DataMart.
4. Streamlit dùng để trình bày kết quả model.
5. Mỗi thành viên đều phải có insight và khuyến nghị hành động.

## 4. Công việc chung giữa các thành viên

| Công việc | Người chính | Người hỗ trợ | Kết quả phải có |
|---|---|---|---|
| Import AdventureWorks vào PostgreSQL | TV4 | Cả nhóm kiểm tra bảng mình dùng | Database chạy được |
| Thiết kế staging/Core DW | TV4 | TV1/TV2/TV3 góp yêu cầu dữ liệu | Dimension/fact đủ dùng |
| Xây mart/customer features | TV1 | TV4 | RFM và customer value dùng được |
| Xây mart/product basket features | TV2 | TV4 | Transaction basket theo order |
| Xây mart/sales time series | TV3 | TV4 | Doanh thu theo tháng/quý/năm |
| Xây macro context mart | TV4 | TV3 nếu cần so sánh với forecast | KPI doanh nghiệp join được với dữ liệu vĩ mô |
| Chuẩn hóa analytics schema | TV4 | TV1/TV2/TV3 | Có nơi lưu output model |
| Tạo chart Superset theo phần mình | TV1/TV2/TV3 | TV4 | Chart phục vụ từng bài phân tích |
| Tổng hợp Superset dashboard | TV4 | TV1/TV2/TV3 | Dashboard thống nhất, có filter, có luồng demo |
| Làm Streamlit model pages | TV1/TV2/TV3 | TV4 | App có page cho từng model |
| Báo cáo cuối | Cả nhóm | TV4 gom format | Báo cáo có insight, chart, model metric, data gap |

## 5. TV1 - Customer Analytics với RFM + K-Means

### Phần phân tích dữ liệu cần làm

TV1 tập trung phân tích khách hàng: khách hàng nào có giá trị cao, hành vi mua khác nhau thế nào, nhóm khách nào nên chăm sóc hoặc upsell.

### Câu hỏi phân tích

1. Khách hàng nào mang lại doanh thu và gross profit cao nhất?
2. Khách hàng mua gần đây hay đã lâu không quay lại?
3. Khách hàng mua thường xuyên hay chỉ mua một vài lần?
4. Nhóm khách hàng nào đóng góp nhiều revenue/gross profit nhất?
5. Doanh nghiệp nên ưu tiên chăm sóc nhóm khách hàng nào?

### Dữ liệu/KPI sử dụng

Dữ liệu:

- `Customer`
- `Person`
- `Store`
- `SalesOrderHeader`
- `SalesOrderDetail`
- `SalesTerritory`
- `dim_customer`
- `fact_sales_order`
- `fact_sales_order_line`
- `mart_customer`

KPI:

- Recency.
- Frequency.
- Monetary.
- Average Order Value.
- Customer Revenue.
- Customer Gross Profit.
- Customer Gross Margin.
- Repeat Purchase Rate proxy.

### Mô hình Data Mining áp dụng

Mô hình: **RFM + K-Means Clustering**.

Cách làm:

1. Tính RFM cho từng customer:
   - Recency = số ngày từ lần mua cuối đến ngày mốc phân tích.
   - Frequency = số đơn hàng hoặc số lần mua.
   - Monetary = tổng net sales hoặc gross profit.
2. Chuẩn hóa feature bằng StandardScaler hoặc MinMaxScaler.
3. Chạy K-Means với nhiều giá trị `k`, ví dụ 3-6.
4. Chọn `k` dựa trên silhouette score và ý nghĩa kinh doanh.
5. Đặt tên segment dễ hiểu:
   - High Value.
   - Loyal.
   - At Risk.
   - New/Promising.
   - Low Value.
6. Lưu output vào `analytics.customer_segment`.

### Visualization phải có

Superset:

1. Top customers by revenue.
2. Top customers by gross profit.
3. Customer value by territory.
4. RFM distribution.

Streamlit:

1. Segment distribution.
2. Revenue/gross profit by segment.
3. Scatter Frequency vs Monetary, tô màu theo segment.
4. Bảng khách hàng High Value/At Risk.
5. Silhouette score và mô tả từng segment.

### Kết quả phải đạt

- Có `mart_customer` và bảng RFM.
- Có output `analytics.customer_segment`.
- Có metric silhouette score.
- Có ít nhất 4 visual customer analytics.
- Có ít nhất 3 insight:
  - nhóm khách hàng giá trị cao.
  - nhóm khách hàng có nguy cơ rời bỏ.
  - segment nên ưu tiên chăm sóc/upsell.

### Phần báo cáo của TV1

1. Vì sao dùng RFM để phân tích khách hàng.
2. Công thức Recency, Frequency, Monetary.
3. Cách chọn số cụm K-Means.
4. Ý nghĩa từng segment.
5. Khuyến nghị chăm sóc/upsell theo segment.

## 6. TV2 - Product & Cross-sell Analytics với Apriori/FP-Growth

### Phần phân tích dữ liệu cần làm

TV2 tập trung phân tích sản phẩm: sản phẩm/category nào bán tốt, sản phẩm nào thường được mua cùng, có thể đề xuất combo hoặc cross-sell nào.

### Câu hỏi phân tích

1. Sản phẩm/category nào bán chạy nhất?
2. Sản phẩm/category nào tạo doanh thu hoặc gross profit cao nhất?
3. Những sản phẩm nào thường xuất hiện cùng trong một đơn hàng?
4. Rule nào có lift/confidence cao và có ý nghĩa kinh doanh?
5. Doanh nghiệp nên đề xuất combo/cross-sell nào?

### Dữ liệu/KPI sử dụng

Dữ liệu:

- `SalesOrderHeader`
- `SalesOrderDetail`
- `Product`
- `ProductCategory`
- `ProductSubcategory`
- `SpecialOffer`
- `dim_product`
- `fact_sales_order_line`
- `mart_product`
- `mart_sales`

KPI:

- Product Revenue.
- Product Quantity Sold.
- Product Gross Profit.
- Product Gross Margin.
- Category Revenue.
- Support.
- Confidence.
- Lift.

### Mô hình Data Mining áp dụng

Mô hình: **Market Basket Analysis bằng Apriori hoặc FP-Growth**.

Cách làm:

1. Tạo transaction basket:
   - mỗi `SalesOrderID` là một transaction.
   - mỗi transaction gồm danh sách product hoặc category.
2. One-hot encode basket để chạy thuật toán.
3. Chạy Apriori hoặc FP-Growth.
4. Tính support, confidence, lift.
5. Lọc rule nhiễu bằng ngưỡng tối thiểu:
   - support đủ lớn.
   - confidence đủ cao.
   - lift > 1.
6. Lưu output vào `analytics.product_association_rule`.

### Visualization phải có

Superset:

1. Top product/category by revenue.
2. Top product/category by quantity.
3. Top product/category by gross profit.
4. Product profitability matrix nếu đủ dữ liệu.

Streamlit:

1. Bảng top association rules.
2. Filter support/confidence/lift.
3. Bar chart top rules by lift.
4. Network graph sản phẩm mua cùng nếu làm kịp.
5. Bảng gợi ý combo/cross-sell.

### Kết quả phải đạt

- Có transaction basket sạch.
- Có output `analytics.product_association_rule`.
- Có ít nhất 10 rule chất lượng sau khi lọc, nếu dữ liệu đủ.
- Có metric support, confidence, lift.
- Có ít nhất 3 insight:
  - sản phẩm/category thường mua cùng.
  - combo có lift cao.
  - đề xuất cross-sell có thể áp dụng.

### Phần báo cáo của TV2

1. Vì sao dùng market basket cho bài toán cross-sell.
2. Cách tạo transaction từ đơn hàng.
3. Ý nghĩa support, confidence, lift.
4. Top rules có ý nghĩa nhất.
5. Khuyến nghị combo/cross-sell.

## 7. TV3 - Sales Forecast Analytics với Time Series Forecast

### Phần phân tích dữ liệu cần làm

TV3 tập trung phân tích doanh thu theo thời gian: xu hướng, tăng trưởng, mùa vụ và dự báo doanh thu kỳ tiếp theo để hỗ trợ lập kế hoạch bán hàng.

### Câu hỏi phân tích

1. Doanh thu tăng/giảm như thế nào theo tháng/quý/năm?
2. Có mùa vụ hoặc chu kỳ rõ không?
3. Gross profit và gross margin biến động như thế nào theo thời gian?
4. Doanh thu kỳ tới có xu hướng tăng hay giảm?
5. Model forecast có tốt hơn baseline không?

### Dữ liệu/KPI sử dụng

Dữ liệu:

- `SalesOrderHeader`
- `SalesOrderDetail`
- `SalesTerritory`
- `dim_date`
- `fact_sales_order`
- `fact_sales_order_line`
- `mart_sales`
- `mart_sales_forecast`

KPI:

- Monthly Revenue.
- Monthly Order Count.
- Monthly Gross Profit.
- Monthly Gross Margin.
- Sales Growth.
- Forecast Error.

### Mô hình Data Mining áp dụng

Mô hình: **Time Series Forecast**.

Baseline:

- Naive forecast.
- Seasonal naive nếu có mùa vụ.
- Moving average.

Model chính:

- Holt-Winters nếu chuỗi có trend/seasonality.
- ARIMA/SARIMA nếu dữ liệu đủ dài và triển khai kịp.

Cách làm:

1. Aggregate doanh thu theo tháng.
2. Chia train/test theo thời gian, không shuffle.
3. Chạy baseline.
4. Chạy model chính.
5. So sánh model bằng MAE, RMSE, WAPE hoặc MAPE.
6. Lưu output vào `analytics.sales_forecast`.

### Visualization phải có

Superset:

1. Revenue trend theo tháng.
2. Gross profit trend theo tháng.
3. Gross margin trend theo tháng.
4. Revenue by territory/category.

Streamlit:

1. Actual vs forecast line chart.
2. Forecast error chart.
3. Bảng metric theo model.
4. Forecast summary cho kỳ tiếp theo.
5. So sánh baseline vs model chính.

### Kết quả phải đạt

- Có `mart_sales_forecast` hoặc view time series.
- Có output `analytics.sales_forecast`.
- Có ít nhất một baseline và một model chính.
- Có metric MAE/RMSE/WAPE hoặc MAPE.
- Có ít nhất 3 insight:
  - xu hướng doanh thu.
  - giai đoạn tăng/giảm đáng chú ý.
  - kỳ vọng/cảnh báo doanh thu kỳ tiếp theo.

### Phần báo cáo của TV3

1. Vì sao dùng time series forecast.
2. Cách aggregate doanh thu theo tháng.
3. Baseline là gì và model chính là gì.
4. Metric đánh giá forecast.
5. Insight từ actual vs forecast và khuyến nghị kế hoạch bán hàng.

## 8. TV4 - Data Platform, BI Integration, Executive Analytics và Macro Context

### Phần phân tích dữ liệu cần làm

TV4 đảm bảo toàn bộ đồ án chạy end-to-end: import dữ liệu, xây Kho Dữ Liệu, kiểm thử dữ liệu, tổng hợp dashboard và phân tích tổng quan. TV4 cũng phụ trách phần liên hệ kinh tế vĩ mô ở mức macro-lite.

Phần phân tích của TV4 gồm:

1. Data Quality Analytics.
2. Reconciliation Analytics.
3. Executive KPI Overview.
4. Macro Context.
5. Dashboard narrative: dẫn người xem từ KPI tổng quan sang từng model của TV1/TV2/TV3.

### Câu hỏi phân tích

1. Dữ liệu AdventureWorks đã được import đầy đủ chưa?
2. Doanh thu/số đơn trong DW có khớp dữ liệu nguồn không?
3. KPI tổng quan của doanh nghiệp đang tốt hay xấu?
4. Revenue, gross profit, gross margin biến động như thế nào?
5. Bối cảnh vĩ mô theo country/period có giúp bổ sung cách đọc xu hướng doanh thu/gross margin không?
6. Dashboard nên trình bày như thế nào để thấy luồng end-to-end?

### Dữ liệu/KPI sử dụng

Dữ liệu/schema:

- PostgreSQL database.
- AdventureWorks source schemas.
- `raw_macro` nếu dùng macro-lite.
- `stg`.
- `core_dw`.
- `mart_sales`.
- `mart_finance`.
- `mart_customer` nền hỗ trợ TV1.
- `mart_product` nền hỗ trợ TV2.
- `mart_sales_forecast` nền hỗ trợ TV3.
- `mart_macro`.
- `analytics`.
- `audit`.

KPI:

- Revenue.
- COGS.
- Gross Profit.
- Gross Margin %.
- Order Count.
- Average Order Value.
- Loss Amount.
- Sales Growth.
- Row Count.
- Missing Key Count.
- Reconciliation Difference.
- Macro indicator value.

### Công việc kỹ thuật và phân tích

1. Import AdventureWorks vào PostgreSQL.
2. Kiểm tra dữ liệu nguồn:
   - số bảng.
   - số dòng.
   - khoảng ngày.
   - null/duplicate ở khóa chính.
   - giá trị âm/bất thường ở giá, số lượng, cost.
3. Xây staging:
   - chuẩn hóa tên cột.
   - chuẩn hóa kiểu dữ liệu.
   - chuẩn hóa ngày/tháng.
   - giữ natural key để truy vết.
4. Xây Core DW tối thiểu:
   - `dim_date`.
   - `dim_product`.
   - `dim_customer`.
   - `dim_geography`.
   - `dim_salesperson`.
   - `fact_sales_order`.
   - `fact_sales_order_line`.
5. Xây mart nền:
   - `mart_sales.sales_monthly_kpi`.
   - `mart_finance.management_pnl_monthly`.
   - `mart_customer.customer_base`.
   - `mart_product.product_sales_summary`.
   - `mart_sales_forecast.monthly_sales_series`.
6. Làm audit/reconciliation:
   - source row count vs DW row count.
   - source revenue vs DW revenue.
   - order count source vs DW.
   - missing date/product/customer keys.
7. Chuẩn hóa `analytics` schema để TV1/TV2/TV3 ghi output.
8. Xây Superset dashboard tổng hợp:
   - Executive Overview.
   - Sales Trend.
   - Customer Segmentation.
   - Market Basket/Cross-sell.
   - Sales Forecast.
   - Macro Context.
9. Hỗ trợ Streamlit:
   - chuẩn hóa connection string.
   - đảm bảo app đọc từ `analytics`/mart, không đọc trực tiếp OLTP.
   - tạo navigation chung nếu cần.

### Liên hệ kinh tế vĩ mô

TV4 phụ trách phần này ở mức gọn, không biến đồ án thành nghiên cứu kinh tế lượng phức tạp.

Mục tiêu:

- Đặt KPI doanh nghiệp trong bối cảnh vĩ mô theo country/period.
- Trả lời câu hỏi: doanh thu/gross margin biến động trong bối cảnh GDP growth, inflation, unemployment hoặc exchange rate như thế nào?
- Chỉ nhận xét tương quan/bối cảnh, không kết luận nguyên nhân.

Cách làm:

1. Chọn 2-4 indicator:
   - GDP growth.
   - inflation.
   - unemployment.
   - exchange rate nếu có dữ liệu phù hợp.
2. Nạp vào `raw_macro`.
3. Chuẩn hóa:
   - country code.
   - period.
   - indicator code.
   - indicator name.
   - value.
   - source.
4. Xây `mart_macro.business_kpi_macro_period`:
   - country.
   - period.
   - revenue.
   - gross_profit.
   - gross_margin.
   - macro_indicator.
   - macro_value.
5. Vẽ Superset Macro Context:
   - revenue/gross margin theo country/period.
   - macro indicator theo country/period.
   - bảng coverage/missing data.
6. Ghi rõ caveat:
   - chỉ là bối cảnh/tương quan mô tả.
   - không kết luận GDP/inflation gây ra doanh thu tăng/giảm.
   - nếu dữ liệu vĩ mô theo năm và ít kỳ thì insight chỉ mang tính tham khảo.

### Visualization phải có

Superset:

1. Executive KPI cards:
   - revenue.
   - gross profit.
   - gross margin.
   - order count.
   - loss amount.
2. Revenue/Gross Profit trend.
3. Gross-level P&L:
   - revenue -> COGS -> gross profit.
4. Data quality dashboard:
   - source rows.
   - DW rows.
   - reconciliation status.
   - missing key count.
5. Macro Context:
   - business KPI by country/period.
   - macro indicator by country/period.
   - coverage/missing data note.
6. Dashboard section/link cho:
   - Customer Segmentation của TV1.
   - Market Basket của TV2.
   - Forecast của TV3.

Streamlit hỗ trợ:

1. Trang Home/Overview nếu cần.
2. Kết nối PostgreSQL dùng chung.
3. Navigation tới 3 page model.
4. Action Summary nếu nhóm muốn gom khuyến nghị.

### Kết quả phải đạt

- PostgreSQL import được AdventureWorks.
- Có staging và Core DW tối thiểu.
- Có mart nền cho 3 bài toán Data Mining.
- Có `analytics` schema cho output model.
- Có audit/reconciliation.
- Có Superset dashboard tổng hợp.
- Có KPI dictionary.
- Có `mart_macro` và Superset Macro Context nếu dữ liệu vĩ mô đủ dùng.
- Có phần Executive/Data Quality/Macro Context để TV4 báo cáo.

### Phần báo cáo của TV4

1. Kiến trúc Kho Dữ Liệu: nguồn -> staging -> core DW -> mart -> analytics -> dashboard/app.
2. Vì sao dashboard không đọc trực tiếp OLTP.
3. Data quality và reconciliation.
4. Executive KPI overview.
5. Liên hệ kinh tế vĩ mô ở mức macro-lite.
6. Cách Superset và Streamlit phối hợp để trình bày kết quả.

## 9. Superset và Streamlit: chia trách nhiệm

### Superset

Superset dùng cho BI dashboard và KPI từ DataMart.

| Khu vực Superset | Người chính | Người hỗ trợ | Dữ liệu đọc từ |
|---|---|---|---|
| Executive Overview | TV4 | TV1/TV2/TV3 | `mart_sales`, `mart_finance` |
| Data Quality/Reconciliation | TV4 | Cả nhóm kiểm tra phần mình | `audit`, `core_dw`, source summary |
| Customer Analytics | TV1 | TV4 | `mart_customer`, `analytics.customer_segment` |
| Product/Cross-sell Analytics | TV2 | TV4 | `mart_product`, `analytics.product_association_rule` |
| Sales Forecast Analytics | TV3 | TV4 | `mart_sales_forecast`, `analytics.sales_forecast` |
| Macro Context | TV4 | TV1/TV3 hỗ trợ KPI/mốc thời gian nếu cần | `mart_macro` |

### Streamlit

Streamlit dùng để demo kết quả Data Mining linh hoạt hơn Superset.

| Trang Streamlit | Người chính | Nội dung |
|---|---|---|
| Home/Overview | TV4 | Giới thiệu ngắn KPI, link tới 3 model |
| Customer Segmentation | TV1 | RFM, segment distribution, scatter, customer list |
| Market Basket | TV2 | Association rules, support/confidence/lift filter, combo recommendation |
| Sales Forecast | TV3 | Actual vs forecast, metric, forecast summary |
| Action Summary | TV4 + cả nhóm | Tổng hợp khuyến nghị từ 3 model |

## 10. Kịch bản báo cáo với giảng viên

Nên báo cáo theo luồng:

1. **TV4 mở đầu**: bài toán doanh nghiệp, kiến trúc Kho Dữ Liệu, dữ liệu đã import, dashboard tổng quan.
2. **TV1**: phần phân tích khách hàng, RFM, K-Means, customer segment và khuyến nghị chăm sóc khách hàng.
3. **TV2**: phần phân tích sản phẩm/cross-sell, Apriori/FP-Growth, luật mua kèm và đề xuất combo.
4. **TV3**: phần phân tích doanh thu theo thời gian, forecast model, metric và dự báo.
5. **TV4 kết nối lại**: Superset dashboard tổng hợp, data quality, reconciliation, macro context, data gap.
6. **Cả nhóm**: kết luận, hạn chế, hướng phát triển.

Mỗi thành viên nên trình bày theo format:

1. Business Question.
2. Phần phân tích dữ liệu.
3. Data & KPI/Feature.
4. Mô hình Data Mining áp dụng.
5. Metric.
6. Visualization.
7. Insight.
8. Action.

### Câu chốt theo từng người

| Thành viên | Câu chốt khi báo cáo |
|---|---|
| TV1 | Em phân tích hành vi khách hàng và dùng RFM + K-Means để biết nhóm nào cần giữ chân, nhóm nào nên upsell. |
| TV2 | Em phân tích sản phẩm và dùng Market Basket để tìm sản phẩm thường mua kèm, từ đó đề xuất combo/cross-sell. |
| TV3 | Em phân tích doanh thu theo thời gian và dùng forecast để dự báo doanh thu kỳ tới, so sánh model với baseline. |
| TV4 | Em xây nền Kho Dữ Liệu, kiểm chứng dữ liệu, tổng hợp dashboard và bổ sung bối cảnh vĩ mô để kết nối insight của cả nhóm. |

## 11. Lịch triển khai đề xuất

| Giai đoạn | TV1 Customer | TV2 Product/Cross-sell | TV3 Forecast | TV4 Platform/BI/Macro |
|---|---|---|---|---|
| Ngày 1-2 | Chốt câu hỏi phân tích khách hàng, feature RFM, kiểm tra bảng customer | Chốt câu hỏi phân tích sản phẩm, transaction basket, kiểm tra bảng product/order | Chốt câu hỏi phân tích forecast, time series grain, kiểm tra sales date/revenue | Import AdventureWorks, kiểm tra source, thiết kế schema |
| Ngày 3-4 | Xây `mart_customer`, RFM bản đầu | Xây product basket transaction | Xây monthly sales series | Xây staging, Core DW, mart nền |
| Ngày 5-6 | Chạy K-Means, chọn k, lưu output | Chạy Apriori/FP-Growth, lọc rule | Chạy baseline + forecast model | Reconciliation, KPI dictionary, Superset skeleton |
| Ngày 7 | Streamlit Customer page, insight segment | Streamlit Market Basket page, combo insight | Streamlit Forecast page, forecast insight | Superset Executive/Data Quality dashboard |
| Ngày 8-9 | Hoàn thiện báo cáo TV1 | Hoàn thiện báo cáo TV2 | Hoàn thiện báo cáo TV3 | Macro Context, tổng hợp Superset, báo cáo phần kiến trúc |
| Ngày 10 | Demo customer model | Demo basket model | Demo forecast model | Demo end-to-end dashboard và kết luận |

## 12. Kết quả cuối cùng phải đạt

1. PostgreSQL chạy được và có dữ liệu AdventureWorks.
2. Có staging, Core DW, DataMart và analytics schema.
3. Có ít nhất 3 output Data Mining chính:
   - `analytics.customer_segment`.
   - `analytics.product_association_rule`.
   - `analytics.sales_forecast`.
4. Có Superset dashboard:
   - Executive Overview.
   - Data Quality/Reconciliation.
   - Customer Analytics.
   - Product/Cross-sell Analytics.
   - Forecast Analytics.
   - Macro Context nếu có dữ liệu.
5. Có Streamlit app:
   - Customer Segmentation.
   - Market Basket.
   - Sales Forecast.
   - Action Summary.
6. Có metric cho từng model:
   - K-Means: silhouette score.
   - Apriori/FP-Growth: support, confidence, lift.
   - Forecast: MAE, RMSE, WAPE hoặc MAPE.
7. Có KPI dictionary và công thức revenue, COGS, gross profit, gross margin.
8. Có audit/reconciliation chứng minh DW khớp nguồn.
9. Có `mart_macro` và phần Macro Context nếu dữ liệu vĩ mô đủ dùng.
10. Có báo cáo nêu rõ data gap về nợ, cashflow, net profit thật và giới hạn của phân tích vĩ mô.
11. Có kịch bản demo end-to-end:
    - source data.
    - staging/Core DW.
    - DataMart.
    - Superset dashboard.
    - Analytics output.
    - Streamlit model pages.
    - recommendation/action.

## 13. Nếu thiếu thời gian thì rút gọn thế nào

Ưu tiên giữ:

1. TV4: import, Core DW tối thiểu, `fact_sales_order_line`, `dim_date`, `dim_product`, `dim_customer`.
2. TV1: RFM + K-Means và Streamlit Customer page.
3. TV2: Market Basket rules và Streamlit Basket page.
4. TV3: Monthly revenue forecast và Streamlit Forecast page.
5. Superset Executive Overview.
6. Reconciliation doanh thu/số đơn.
7. Macro Context tối thiểu nếu có dữ liệu vĩ mô.

Có thể bỏ hoặc để hướng phát triển:

- Network graph market basket.
- Forecast theo từng product/category.
- Macro Context nếu không kịp lấy dữ liệu vĩ mô.
- Operations mart phức tạp.
- Delivery delay classification.
- Anomaly detection nâng cao.
- MLflow/Prefect/dbt.
- Nợ, cashflow, DSO/DPO, net profit margin thật.
