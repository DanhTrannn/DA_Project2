# Phân công công việc đồ án Kho Dữ Liệu và Data Mining - Nhóm 4 thành viên

Tài liệu này chia công việc dựa trên `PLAN.md` hiện tại. Mục tiêu là làm được một đồ án end-to-end: nạp dữ liệu AdventureWorks vào PostgreSQL, xây Core Data Warehouse, xây DataMart, tính KPI, dựng Superset dashboard, làm Streamlit app cho Data Mining và viết báo cáo insight.

Phạm vi đã chốt:

- Có làm liên hệ kinh tế vĩ mô ở mức **macro-lite**: dùng 2-4 chỉ số như GDP growth, inflation, unemployment hoặc exchange rate để bổ sung bối cảnh cho doanh thu/gross margin theo quốc gia và thời gian.
- Phần vĩ mô chỉ dùng để phân tích bối cảnh và tương quan mô tả, không kết luận nhân quả tuyệt đối.
- Không mô phỏng nợ, dòng tiền, DSO/DPO, lợi nhuận ròng hoặc lãi vay vì AdventureWorks không có dữ liệu kế toán/thanh toán thật.
- Tài chính chỉ làm ở mức gross-level: revenue, COGS, gross profit, gross margin, loss amount.
- Superset dùng cho BI dashboard từ DataMart.
- Streamlit dùng cho visualize Data Mining từ bảng `analytics` và các mart liên quan.
- Dashboard/app trực quan là đầu ra bắt buộc, không chỉ làm database hoặc notebook.

## 1. Kiến trúc đề xuất

```text
AdventureWorks OLTP + dữ liệu vĩ mô gọn
        |
        v
PostgreSQL Staging + Raw Macro
        |
        v
Core Data Warehouse
        |
        v
DataMart nghiệp vụ + Macro Context Mart
        |
        +--------------------+
        |                    |
        v                    v
Superset BI Dashboard      Data Mining / Analytics
        |                    |
        |                    v
        |             Streamlit Mining App
        |                    |
        +---------+----------+
                  v
        Báo cáo phân tích và khuyến nghị
```

Ý nghĩa từng lớp:

| Lớp | Mục đích |
|---|---|
| AdventureWorks OLTP | Dữ liệu nguồn gốc về bán hàng, sản phẩm, khách hàng, mua hàng, tồn kho, sản xuất |
| Raw Macro | Dữ liệu vĩ mô gọn theo country/period/indicator/value/source, có thể lấy từ CSV hoặc API công khai |
| Staging | Làm sạch, chuẩn hóa tên cột, kiểu dữ liệu, status code, ngày tháng |
| Core DW | Mô hình dimension/fact dùng chung, đảm bảo KPI tính nhất quán |
| DataMart | Bảng nghiệp vụ phục vụ Superset dashboard và câu hỏi phân tích cụ thể |
| Macro Context Mart | Mart nối KPI doanh nghiệp với chỉ số vĩ mô theo country/period để phân tích bối cảnh |
| Analytics | Feature table, kết quả Data Mining, forecast, anomaly, macro relation, recommendation |
| Superset BI Dashboard | Trình bày KPI quản trị từ DataMart: Executive, Sales, Finance, Operations, Customer, Macro Context |
| Streamlit Mining App | Trình bày kết quả Data Mining: segmentation, market basket, anomaly, forecast, Action Center |
| Báo cáo | Giải thích insight, giới hạn dữ liệu, khuyến nghị hành động |

## 2. Nguyên tắc làm chung

1. Superset không truy vấn trực tiếp OLTP; Superset đọc từ DataMart.
2. Streamlit không truy vấn trực tiếp OLTP; Streamlit đọc từ `analytics` và các mart liên quan.
3. Mỗi KPI phải có công thức, nguồn dữ liệu, grain và cách kiểm chứng.
4. Mỗi fact phải có grain rõ ràng trước khi viết SQL.
5. Mọi kết quả quan trọng phải có kiểm tra đối chiếu với dữ liệu nguồn.
6. Mỗi biểu đồ phải trả lời một câu hỏi kinh doanh, không vẽ chỉ để trang trí.
7. Các chỉ số thiếu dữ liệu thật phải ghi là data gap, không trình bày như kết quả chính thức.
8. Phân tích vĩ mô chỉ ghi nhận tương quan/bối cảnh, không viết như bằng chứng nhân quả.

## 3. Phân công tổng quan

| Thành viên | Vai trò | Phần chịu trách nhiệm chính | Kết quả cuối phải có |
|---|---|---|---|
| Thành viên 1 | Data Platform, Core DW và Raw Macro | PostgreSQL, import dữ liệu, staging, dimension/fact, raw macro, kiểm thử dữ liệu | Database chạy được, Core DW đúng grain, macro data chuẩn hóa, reconciliation pass |
| Thành viên 2 | Sales, Finance Gross-Level, Customer và KPI | DataMart bán hàng, tài chính gross-level, khách hàng, KPI dictionary, KPI theo country/period, chart Superset nhóm sales/finance/customer | KPI tính được, mart sales/finance/customer, dữ liệu business KPI đủ để join macro |
| Thành viên 3 | Operations, Macro Context và Superset Dashboard | DataMart mua hàng/tồn kho/sản xuất, `mart_macro`, Superset dashboard tổng hợp | Mart operations/production/macro, Superset dashboard có Macro Context và biểu đồ vận hành |
| Thành viên 4 | Data Mining, Macro Relation, Streamlit App, Recommendation và Báo cáo | Segmentation, market basket, anomaly, forecast, macro relation, Streamlit app, recommendation, báo cáo cuối | Model output lưu được, bảng tương quan macro, Streamlit Action Center, model report, báo cáo insight |

## 4. Thành viên 1 - Data Platform và Core Data Warehouse

### Mục tiêu

Tạo nền dữ liệu đáng tin cậy để cả nhóm xây DataMart, Superset dashboard, Streamlit app và Data Mining. Đây là phần chứng minh đồ án có sử dụng Kho Dữ Liệu thật, không chỉ truy vấn báo cáo trực tiếp từ OLTP.

### Câu hỏi cần trả lời

1. Dữ liệu AdventureWorks đã được import đúng vào PostgreSQL chưa?
2. Các bảng nguồn có bao nhiêu dòng, khoảng ngày nào, có lỗi null/duplicate/giá trị âm bất thường không?
3. Core DW có đủ dimension/fact để các mart dùng lại không?
4. Tổng doanh thu, số đơn, số dòng bán trong DW có khớp với dữ liệu nguồn không?
5. Dữ liệu vĩ mô có map được với country/period của AdventureWorks không?

### Làm gì

1. Dựng PostgreSQL và import AdventureWorks.
2. Kiểm tra các schema nguồn chính:
   - Sales
   - Production
   - Purchasing
   - Person
   - HumanResources
3. Làm profiling dữ liệu nguồn:
   - số dòng từng bảng
   - khoảng ngày dữ liệu
   - số lượng null ở cột quan trọng
   - duplicate key
   - giá trị âm hoặc bằng 0 bất thường ở giá, số lượng, chi phí
4. Xây staging:
   - chuẩn hóa tên cột
   - chuẩn hóa kiểu dữ liệu
   - chuẩn hóa status code
   - tính lại line total hoặc total due nếu cần đối chiếu
5. Xây Core DW:
   - `dim_date`
   - `dim_product`
   - `dim_customer`
   - `dim_geography`
   - `dim_salesperson`
   - `dim_vendor`
   - `dim_employee`
   - `dim_promotion`
   - `dim_ship_method`
   - `dim_currency`
   - `fact_sales_order_line`
   - `fact_sales_order`
   - `fact_purchase_order_line`
   - `fact_inventory_transaction`
   - `fact_inventory_snapshot`
   - `fact_work_order`
   - `fact_work_order_operation`
   - `fact_sales_quota`
6. Tính COGS cho dòng bán hàng theo standard cost tại thời điểm bán.
7. Tạo audit/reconciliation để kiểm tra dữ liệu.
8. Nạp và chuẩn hóa dữ liệu vĩ mô gọn:
   - `raw_macro.macro_observation`
   - `dim_macro_indicator`
   - `fact_macro_observation`
   - chuẩn hóa country code, period, indicator code, value, unit, source
9. Tạo index cơ bản cho các khóa ngày, sản phẩm, khách hàng, vendor, country/period.

### Làm như nào

1. Import dữ liệu nguồn trước, sau đó kiểm tra số bảng và số dòng để chắc dữ liệu không thiếu.
2. Với staging, chỉ xử lý các bảng cần cho đồ án thay vì làm toàn bộ AdventureWorks.
3. Với dimension, giữ cả surrogate key và natural key để truy vết về nguồn.
4. Với fact, ghi rõ grain:
   - `fact_sales_order_line`: một dòng sản phẩm trong một đơn bán.
   - `fact_sales_order`: một đơn bán.
   - `fact_purchase_order_line`: một dòng sản phẩm trong đơn mua.
   - `fact_inventory_snapshot`: một sản phẩm tại một location tại một ngày/chốt kỳ.
   - `fact_work_order`: một lệnh sản xuất.
5. Với COGS, join sản phẩm với lịch sử giá vốn theo `order_date` nằm trong khoảng hiệu lực của cost history.
6. Với reconciliation, so sánh các chỉ số:
   - số đơn bán nguồn và fact
   - số dòng bán nguồn và fact
   - tổng `LineTotal` hoặc doanh thu tính lại
   - số đơn mua nguồn và fact
   - số work order nguồn và fact
7. Với dữ liệu vĩ mô, chỉ giữ bộ chỉ số nhỏ và dễ giải thích:
   - GDP growth
   - inflation
   - unemployment
   - exchange rate nếu có dữ liệu phù hợp
8. Kiểm tra coverage của macro theo country/period trước khi cho TV3/TV4 dùng.

### Kết quả phải đạt được

- PostgreSQL có dữ liệu AdventureWorks và các schema phân tích.
- Staging sạch, dễ dùng cho bước sau.
- Core DW có dimension/fact chính.
- Có bảng hoặc báo cáo profiling.
- Có bảng hoặc báo cáo reconciliation.
- Có `raw_macro` và bảng macro chuẩn hóa đủ để xây `mart_macro`.
- Các thành viên khác có thể dùng Core DW để xây mart mà không phải tự xử lý dữ liệu nguồn.

### Biểu đồ/bảng cần hỗ trợ

- Data quality summary: số dòng, null, duplicate, lỗi dữ liệu.
- Reconciliation table: source value, DW value, difference, status.
- Line chart doanh thu theo tháng để kiểm tra dữ liệu bán hàng có hợp lý không.
- Macro coverage table: country, period, indicator, số kỳ có dữ liệu, số kỳ thiếu.

### Tiêu chí nghiệm thu

- Import dữ liệu chạy được từ đầu.
- Reconciliation các chỉ số chính phải pass hoặc có giải thích rõ nếu lệch.
- Các fact có grain rõ ràng.
- Superset dashboard và Streamlit app không cần đọc trực tiếp bảng OLTP.

## 5. Thành viên 2 - Sales, Finance Gross-Level, Customer và KPI

### Mục tiêu

Trả lời các câu hỏi kinh doanh về doanh thu, lợi nhuận gộp, lỗ/lãi theo sản phẩm/khách hàng/khu vực, giá trị khách hàng và hiệu quả bán hàng.

### Câu hỏi cần trả lời

1. Doanh thu tăng hay giảm theo tháng/quý/năm?
2. Sản phẩm, category, khách hàng, khu vực nào tạo doanh thu và gross profit cao nhất?
3. Dòng bán hàng nào bị lỗ hoặc margin thấp?
4. Chiết khấu ảnh hưởng thế nào đến gross margin?
5. Khách hàng nào có giá trị cao và nên ưu tiên chăm sóc?
6. KPI doanh thu/gross margin theo country/period có đủ grain để liên hệ với bối cảnh vĩ mô không?

### Làm gì

1. Xây `mart_sales`:
   - sales monthly KPI
   - product profitability
   - customer profitability
   - territory profitability
   - salesperson performance
2. Xây `mart_finance` ở mức gross-level:
   - management P&L monthly
   - profit/loss by product
   - profit/loss by customer
   - profit status: loss, low_margin, profitable
3. Xây `mart_customer`:
   - customer RFM
   - customer value
   - customer profitability
   - repeat purchase proxy
   - salesperson quota attainment nếu đủ dữ liệu
4. Tạo business KPI theo country/period để phục vụ `mart_macro`:
   - revenue by country/month hoặc country/year
   - quantity by country/month hoặc country/year
   - gross profit/gross margin by country/month hoặc country/year
   - order count by country/month hoặc country/year
5. Định nghĩa KPI:
   - Gross Sales
   - Discount Amount
   - Net Sales
   - Tax Amount
   - Freight Amount
   - Total Due
   - COGS
   - Gross Profit
   - Gross Margin %
   - Sales Growth
   - Average Order Value
   - Loss Amount
   - Loss-making Line Ratio
6. Viết KPI dictionary:
   - tên KPI
   - công thức
   - bảng/cột nguồn
   - grain
   - ý nghĩa kinh doanh
   - cách kiểm chứng
7. Ghi rõ data gap:
   - không làm nợ vay
   - không làm phải thu/phải trả
   - không làm DSO/DPO
   - không làm cashflow
   - không làm net profit margin thật

### Làm như nào

1. Lấy dữ liệu từ Core DW, không lấy trực tiếp từ bảng OLTP.
2. Tính doanh thu ở mức dòng đơn trước, sau đó aggregate lên tháng/sản phẩm/khách hàng/khu vực.
3. Tính `Gross Sales = OrderQty * UnitPrice`.
4. Tính `Discount Amount = OrderQty * UnitPrice * UnitPriceDiscount`.
5. Tính `Net Sales = Gross Sales - Discount Amount` hoặc dùng `LineTotal` nếu đã đối chiếu đúng.
6. Tính `COGS = OrderQty * StandardCost tại thời điểm OrderDate`.
7. Tính `Gross Profit = Net Sales - COGS`.
8. Tính `Gross Margin % = Gross Profit / Net Sales`.
9. Gắn trạng thái lời/lỗ:
   - `loss` nếu gross profit < 0
   - `low_margin` nếu gross margin thấp hơn ngưỡng nhóm tự chọn
   - `profitable` nếu có gross profit và margin tốt
10. Với RFM:
   - Recency: số ngày từ lần mua cuối đến ngày mốc phân tích.
   - Frequency: số đơn hoặc số lần mua.
   - Monetary: tổng net sales hoặc gross profit.

### Kết quả phải đạt được

- `mart_sales` trả lời được câu hỏi doanh thu và lợi nhuận.
- `mart_finance` trình bày được P&L gross-level, không giả lập kế toán.
- `mart_customer` có RFM và customer value.
- Có KPI doanh nghiệp theo country/period để TV3/TV4 join với dữ liệu vĩ mô.
- KPI dictionary hoàn chỉnh cho các KPI chính.
- Có ít nhất 5 insight kinh doanh từ sales/finance/customer.

### Biểu đồ Superset phải làm

Thành viên 2 tạo các dataset/chart Superset cho nhóm Sales, Finance và Customer. Các chart này sẽ được thành viên 3 gom vào Superset dashboard tổng hợp.

1. Executive KPI cards:
   - total revenue
   - gross profit
   - gross margin %
   - order count
   - loss amount
2. Revenue & Gross Profit Trend:
   - line chart doanh thu và gross profit theo tháng
3. Product Profitability:
   - top sản phẩm lãi cao nhất
   - top sản phẩm lỗ hoặc margin thấp nhất
4. Sales by Territory:
   - doanh thu/gross profit theo khu vực hoặc quốc gia
   - xu hướng revenue/gross margin theo country để dùng trong Macro Context
5. Customer Value:
   - top khách hàng theo revenue/gross profit
   - scatter plot frequency vs monetary nếu làm được
6. Salesperson Performance:
   - doanh thu/gross profit theo salesperson
7. Finance Gross-Level:
   - waterfall hoặc stacked bar: revenue -> COGS -> gross profit
   - note rõ phần data gap về nợ/dòng tiền/lợi nhuận ròng

### Tiêu chí nghiệm thu

- KPI tính nhất quán với Core DW.
- Có thể giải thích sản phẩm/khách hàng/khu vực nào lời hoặc lỗ.
- Không trình bày net profit, nợ, dòng tiền như dữ liệu thật.
- Biểu đồ Superset có tiêu đề, đơn vị, nguồn dữ liệu và insight đi kèm.

## 6. Thành viên 3 - Operations, Macro Context và Superset Dashboard tổng hợp

### Mục tiêu

Phân tích vận hành doanh nghiệp gồm mua hàng, nhà cung cấp, tồn kho, sản xuất, phế phẩm; xây thêm Macro Context Mart để đặt KPI doanh nghiệp trong bối cảnh vĩ mô; đồng thời dựng Superset dashboard tổng hợp để demo kết quả BI của cả nhóm.

### Câu hỏi cần trả lời

1. Nhà cung cấp nào có chi phí mua hàng cao, lead time dài hoặc tỷ lệ rejected cao?
2. Sản phẩm nào có nguy cơ thiếu hàng hoặc tồn kho quá cao?
3. Sản xuất có vấn đề ở sản phẩm/công đoạn nào?
4. Scrap rate và cost variance đang tập trung ở đâu?
5. Doanh thu/gross margin theo quốc gia biến động trong bối cảnh GDP growth, inflation, unemployment hoặc exchange rate như thế nào?
6. Superset dashboard nên trình bày theo luồng nào để người xem hiểu nhanh từ tổng quan đến vận hành và Macro Context?

### Làm gì

1. Xây `mart_supply_chain`:
   - purchase monthly KPI
   - vendor scorecard
   - inventory snapshot
   - inventory turnover monthly
   - stockout risk
2. Xây `mart_production`:
   - work order KPI
   - scrap analysis
   - operation cost variance
   - production delay risk
3. Tính KPI vận hành:
   - Purchase Spend
   - Average Purchase Price
   - Price Variance
   - Received Rate
   - Rejected Rate
   - Vendor Lead Time
   - Inventory Value
   - Inventory Turnover
   - DIO proxy
   - Safety Stock Gap
   - Reorder Point Gap
   - Scrap Rate
   - Production Delay Days
   - Cost Variance
4. Phân nhóm vendor:
   - strategic
   - standard
   - quality risk
   - lead-time risk
5. Thiết kế Superset dashboard tổng hợp:
   - Executive Overview
   - Sales & Profitability
   - Customer Analytics
   - Operations
   - Finance Gross-Level
   - Macro Context
6. Xây `mart_macro`:
   - `macro_observation_standardized`
   - `business_kpi_macro_period`
   - join KPI từ TV2 với macro theo country/period
7. Phối hợp với thành viên 4 để đặt link hoặc ảnh chụp/ghi chú dẫn sang Streamlit app cho Forecast, Macro Relation và Action Center nếu cần demo liền mạch.

### Làm như nào

1. Lấy dữ liệu mua hàng từ fact purchase order line và dimension vendor/product/date.
2. Tính `Rejected Rate = RejectedQty / ReceivedQty`.
3. Tính `Received Rate = ReceivedQty / OrderQty`.
4. Tính vendor lead time từ order date, due date hoặc received date tùy dữ liệu có sẵn.
5. Tính inventory value bằng quantity on hand nhân với standard cost.
6. Tính safety stock gap bằng quantity on hand trừ safety stock level.
7. Tính reorder point gap bằng quantity on hand trừ reorder point.
8. Tính scrap rate bằng scrapped quantity chia order quantity.
9. Tính production delay days bằng end date trừ due date.
10. Với `mart_macro`, ưu tiên join theo country + year nếu dữ liệu vĩ mô chỉ có theo năm; nếu có dữ liệu tháng thì join theo country + month.
11. Macro Context phải có ghi chú rõ: đây là bối cảnh/tương quan mô tả, không phải kết luận nhân quả.
12. Với Superset dashboard, gom chart BI của thành viên 2, chart operations và chart macro thành một luồng demo:
    - tổng quan KPI
    - đi sâu sales/finance/customer
    - đi sâu operations
    - đặt KPI doanh nghiệp vào Macro Context
    - kết thúc bằng phần dẫn sang Streamlit app để xem forecast/anomaly/recommendation

### Kết quả phải đạt được

- `mart_supply_chain` có dữ liệu vendor, purchase, inventory.
- `mart_production` có dữ liệu work order, scrap, cost variance.
- `mart_macro` có dữ liệu KPI doanh nghiệp kết hợp chỉ số vĩ mô theo country/period.
- Superset dashboard tổng hợp có bố cục rõ ràng.
- Có ít nhất 5 biểu đồ vận hành.
- Có ít nhất 1 khu vực Macro Context trong Superset.
- Có ít nhất 3 insight vận hành: vendor rủi ro, sản phẩm thiếu hàng, scrap/cost variance bất thường.

### Biểu đồ Superset phải làm

1. Vendor Scorecard:
   - rejected rate theo vendor
   - purchase spend theo vendor
   - average lead time theo vendor
   - bảng vendor segment
2. Inventory Health:
   - sản phẩm dưới safety stock
   - inventory value theo category
   - stockout risk table
3. Production Quality:
   - scrap rate theo tháng/sản phẩm/reason
   - cost variance theo công đoạn hoặc sản phẩm
   - production delay table
4. Superset Dashboard Navigation:
   - các trang hoặc khu vực Superset dashboard được sắp theo luồng demo dễ hiểu
   - filter thống nhất theo thời gian, product category, territory nếu công cụ hỗ trợ
5. Macro Context:
   - revenue/gross margin theo country/period
   - GDP growth/inflation/unemployment hoặc exchange rate theo country/period
   - bảng ghi chú coverage và caveat không kết luận nhân quả

### Tiêu chí nghiệm thu

- Biểu đồ vận hành trả lời được câu hỏi kinh doanh cụ thể.
- Biểu đồ Macro Context cho thấy được bối cảnh vĩ mô đi cùng KPI doanh nghiệp nhưng không diễn giải quá mức.
- Superset dashboard không đọc trực tiếp từ OLTP.
- Superset dashboard có tiêu đề, đơn vị, filter và ghi chú data gap khi cần.
- Người xem có thể demo từ overview đến operations, sau đó chuyển sang Streamlit cho mining mà không bị rời rạc.

## 7. Thành viên 4 - Data Mining, Macro Relation, Streamlit App, Recommendation và Báo cáo cuối

### Mục tiêu

Triển khai các bài toán Data Mining có giá trị thực tế, lưu kết quả vào PostgreSQL, xây Streamlit app để visualize kết quả model và biến kết quả thành khuyến nghị hành động cho doanh nghiệp.

### Câu hỏi cần trả lời

1. Có thể phân nhóm khách hàng theo hành vi mua không?
2. Sản phẩm nào thường được mua cùng để gợi ý cross-sell/combo?
3. Dòng bán hàng nào bất thường do discount cao, margin thấp hoặc bán lỗ?
4. Doanh thu các kỳ tới có xu hướng như thế nào?
5. KPI doanh nghiệp có tương quan mô tả nào với GDP growth, inflation, unemployment hoặc exchange rate không?
6. Từ KPI và model output, doanh nghiệp nên ưu tiên hành động gì?

### Làm gì

1. Tạo feature table:
   - customer RFM
   - market basket transactions
   - sales line anomaly features
   - monthly sales time series
   - macro KPI relation features nếu dữ liệu đủ coverage
   - delivery delay features nếu target đủ dùng
2. Chạy Customer Segmentation:
   - thuật toán: RFM + K-Means
   - metric: silhouette score
   - output: customer segment
3. Chạy Market Basket:
   - thuật toán: FP-Growth hoặc Apriori
   - metric: support, confidence, lift
   - output: product association rules
4. Chạy Sales Anomaly Detection:
   - thuật toán: Isolation Forest
   - rule bổ sung: bán lỗ, discount cao, margin thấp, giao trễ
   - output: anomaly list có severity và reason
5. Chạy Sales Forecast:
   - baseline: seasonal naive hoặc moving average
   - model chính: Holt-Winters, ARIMA hoặc SARIMA
   - metric: MAE, RMSE, WAPE
   - output: actual vs forecast
6. Chạy delivery delay risk scoring nếu dữ liệu đủ:
   - nếu target có đủ hai lớp thì dùng Logistic Regression hoặc tree-based model đơn giản
   - nếu target chỉ có một lớp thì dùng rule fallback và ghi rõ giới hạn
7. Chạy macro relation mô tả:
   - dùng `mart_macro.business_kpi_macro_period`
   - tính correlation hoặc lag correlation nếu số kỳ đủ
   - output: `analytics.macro_kpi_relation`
   - ghi rõ sample size, missing data và caveat không kết luận nhân quả
8. Tạo recommendation/action center:
   - gom anomaly, low-margin product, stockout risk, forecast risk
   - gán priority high/medium/low
   - ghi reason, expected impact, suggested action
9. Xây Streamlit app:
   - trang Customer Segmentation
   - trang Market Basket
   - trang Sales Anomaly
   - trang Sales Forecast
   - trang Macro Relation nếu đủ thời gian
   - trang Action Center
10. Viết model report và hỗ trợ báo cáo cuối.

### Làm như nào

1. Tất cả feature phải lấy từ DataMart hoặc Core DW đã chuẩn hóa.
2. Với segmentation:
   - chuẩn hóa RFM trước khi chạy K-Means.
   - thử vài giá trị k và chọn k theo silhouette + ý nghĩa kinh doanh.
   - đặt tên segment dễ hiểu, ví dụ high value, loyal, at risk, low value.
3. Với market basket:
   - tạo transaction theo sales order.
   - mỗi order là một tập sản phẩm.
   - lọc rule có lift/confidence đủ cao để tránh rule nhiễu.
4. Với anomaly:
   - tạo feature gồm quantity, unit price, discount, margin, freight, delivery days.
   - kết hợp model score với business rules để giải thích được lý do.
5. Với forecast:
   - aggregate doanh thu theo tháng.
   - chia train/test theo thời gian.
   - so sánh model với baseline.
   - lưu forecast kèm model name, run date, horizon và metric.
6. Với macro relation:
   - chỉ tính khi số kỳ quan sát đủ tối thiểu để có ý nghĩa mô tả.
   - không dùng correlation để kết luận "vĩ mô gây ra doanh thu tăng/giảm".
   - ưu tiên diễn giải như: "trong mẫu dữ liệu này, giai đoạn inflation cao đi kèm gross margin thấp hơn".
7. Với recommendation:
   - không chỉ lưu score; mỗi dòng phải có action cụ thể.
   - ví dụ: "review discount", "adjust price", "check inventory", "prioritize customer", "review vendor".
8. Với Streamlit:
   - kết nối PostgreSQL bằng SQLAlchemy hoặc connector tương đương.
   - đọc dữ liệu từ `analytics` và các mart liên quan.
   - dùng Plotly để vẽ line chart, bar chart, scatter plot và table.
   - có sidebar filter tối thiểu theo thời gian, segment, severity hoặc ngưỡng confidence/lift nếu phù hợp.

### Kết quả phải đạt được

- Có ít nhất 4 output Data Mining:
  - customer segment
  - product association rules
  - sales anomaly
  - sales forecast
- Có thêm delivery risk scoring hoặc rule fallback nếu dữ liệu cho phép.
- Có `analytics.macro_kpi_relation` nếu macro coverage đủ dùng.
- Kết quả model được lưu thành bảng analytics.
- Có metric đánh giá model.
- Có recommendation/action center.
- Có Streamlit app visualize được kết quả Data Mining.
- Có model report giải thích bằng ngôn ngữ kinh doanh.

### Streamlit app phải làm

1. Customer Segment:
   - số khách hàng theo segment
   - revenue/gross profit theo segment
   - scatter RFM nếu làm được
2. Market Basket:
   - bảng top rules theo lift/confidence
   - filter theo support, confidence, lift
   - network chart sản phẩm mua cùng nếu công cụ hỗ trợ
3. Sales Anomaly:
   - bảng anomaly có severity/reason
   - số anomaly theo reason
   - scatter discount vs gross margin, highlight anomaly nếu làm được
4. Forecast:
   - actual revenue vs forecast
   - forecast error theo tháng nếu có backtesting
   - forecast summary table
5. Macro Relation nếu đủ thời gian:
   - bảng correlation theo country/indicator/KPI
   - line chart KPI doanh nghiệp so với chỉ số vĩ mô đã chuẩn hóa
   - caveat về sample size và không kết luận nhân quả
6. Action Center:
   - recommendation
   - priority
   - reason
   - expected impact
   - confidence
   - suggested action

### Tiêu chí nghiệm thu

- Mỗi model trả lời một câu hỏi kinh doanh rõ ràng.
- Forecast có baseline hoặc metric sai số.
- Kết quả model lưu được vào PostgreSQL, không chỉ in ra notebook/terminal.
- Streamlit app đọc được từ PostgreSQL hoặc bảng output đã lưu.
- Recommendation có action cụ thể, không chỉ có score.
- Macro relation nếu làm phải có sample size và caveat rõ ràng.
- Báo cáo cuối giải thích được model bằng ngôn ngữ kinh doanh.

## 8. Superset dashboard và Streamlit app tối thiểu phải có

Cuối kỳ nhóm cần có cả Superset dashboard và Streamlit app. Hai phần này dùng chung PostgreSQL nhưng phục vụ mục đích khác nhau.

### 8.1 Superset dashboard

Superset đọc từ DataMart, dùng để trình bày KPI quản trị và phân tích nghiệp vụ.

| Trang/khu vực Superset | Biểu đồ/KPI bắt buộc | Người chịu trách nhiệm chính |
|---|---|---|
| Executive Overview | revenue, gross profit, gross margin, order count, warning summary | Thành viên 2 + Thành viên 3 |
| Sales & Profitability | revenue trend, gross profit trend, sales by category/territory, loss-making products, discount vs margin | Thành viên 2 |
| Customer Analytics | top customers, RFM distribution, customer value, revenue/gross profit by customer group | Thành viên 2 |
| Finance Gross-Level | revenue -> COGS -> gross profit, loss amount, data gap note | Thành viên 2 |
| Operations | vendor scorecard, inventory health, scrap rate, cost variance | Thành viên 3 |
| Macro Context | revenue/gross margin theo country/period, GDP growth/inflation/unemployment/exchange rate, caveat không kết luận nhân quả | Thành viên 3 + Thành viên 4 |

### 8.2 Streamlit app

Streamlit đọc từ `analytics` và các mart liên quan, dùng để trình bày kết quả Data Mining và khuyến nghị.

| Trang Streamlit | Visualize bắt buộc | Người chịu trách nhiệm chính |
|---|---|---|
| Customer Segmentation | số khách theo segment, revenue/gross profit theo segment, scatter RFM nếu làm được | Thành viên 4 |
| Market Basket | top association rules, filter support/confidence/lift | Thành viên 4 |
| Sales Anomaly | anomaly table, anomaly reason chart, discount vs margin scatter nếu làm được | Thành viên 4 |
| Forecast | actual vs forecast, forecast error, forecast summary | Thành viên 4 |
| Macro Relation | correlation table, KPI vs macro normalized line chart nếu đủ coverage | Thành viên 4 |
| Action Center | recommendation, priority, reason, expected impact, suggested action | Thành viên 4 |

## 9. Lịch triển khai đề xuất

| Giai đoạn | Thành viên 1 | Thành viên 2 | Thành viên 3 | Thành viên 4 |
|---|---|---|---|---|
| Ngày 1-2 | Dựng PostgreSQL, import dữ liệu, kiểm tra nguồn, chốt macro indicator | Chốt KPI sales/finance/customer | Chốt KPI operations/Superset/Macro Context | Chốt use case Data Mining/Streamlit/macro relation |
| Ngày 3-4 | Staging, profiling, Core DW bản đầu, nạp `raw_macro` | Mart sales/finance/customer bản đầu, KPI country/period | Mart supply chain/production bản đầu | Feature table mining |
| Ngày 5-6 | Reconciliation, tối ưu Core DW, kiểm tra macro coverage | KPI dictionary, insight sales | Insight operations, Superset layout, `mart_macro` | Segmentation, basket, anomaly |
| Ngày 7 | Hỗ trợ tích hợp dữ liệu | Chart Superset sales/finance/customer | Chart Superset operations, Macro Context, dashboard tổng hợp | Forecast, recommendation, macro relation |
| Ngày 8-9 | Runbook, kiểm thử dữ liệu | Viết phần KPI/insight | Hoàn thiện Superset demo | Streamlit app, model report, Action Center |
| Ngày 10 | Demo kỹ thuật | Demo KPI và mart | Demo Superset dashboard + Macro Context | Demo Streamlit mining và báo cáo cuối |

## 10. Kết quả cuối cùng cả nhóm phải đạt

1. PostgreSQL chạy được và có dữ liệu AdventureWorks.
2. Có staging và Core DW với dimension/fact chính.
3. Có ít nhất 4 DataMart hoàn chỉnh:
   - `mart_sales`
   - `mart_finance`
   - `mart_supply_chain`
   - `mart_production`
4. Có thêm `mart_customer` để phục vụ RFM và customer analytics.
5. Có thêm `mart_macro` để liên hệ KPI doanh nghiệp với bối cảnh vĩ mô theo country/period.
6. KPI doanh thu, lợi nhuận gộp, lỗ/lãi, tồn kho, mua hàng, sản xuất tính được và kiểm chứng được.
7. Có ít nhất 4 output Data Mining:
   - customer segmentation
   - market basket rules
   - sales anomaly
   - sales forecast
8. Có thêm `analytics.macro_kpi_relation` nếu macro coverage đủ dùng.
9. Có Superset dashboard thật để trình bày KPI/DataMart/Macro Context.
10. Có Streamlit app thật để trình bày Data Mining và Action Center.
11. Có kiểm thử dữ liệu và reconciliation.
12. Có báo cáo nêu rõ data gap về nợ, dòng tiền, lợi nhuận ròng, các chỉ số thanh khoản và giới hạn của phân tích vĩ mô.
13. Có kịch bản demo từ dữ liệu -> Core DW -> DataMart -> Superset -> Analytics -> Streamlit -> Recommendation.

## 11. Phần có thể rút gọn nếu thiếu thời gian

Ưu tiên giữ:

1. Core DW tối thiểu: `dim_date`, `dim_product`, `dim_customer`, `dim_geography`, `fact_sales_order_line`.
2. `mart_sales` và KPI doanh thu/lợi nhuận gộp.
3. Superset dashboard Executive + Sales.
4. RFM/K-Means.
5. Market Basket.
6. Sales Anomaly.
7. Sales Forecast.
8. Macro-lite tối thiểu: 2-3 indicator, `mart_macro`, một biểu đồ Superset Macro Context.
9. Streamlit app tối thiểu cho segmentation, anomaly, forecast và recommendation.

Có thể bỏ hoặc để hướng phát triển:

- Delivery delay classification nếu target không đủ hai lớp.
- Model dự đoán scrap phức tạp.
- Dự báo theo từng sản phẩm nếu dữ liệu quá thưa.
- Deep learning.
- MLflow/Prefect/dbt nếu không đủ thời gian.
- Macro relation nâng cao hoặc lag correlation nếu dữ liệu vĩ mô quá ít kỳ.
- Nợ, cashflow, DSO/DPO, net profit margin thật.
