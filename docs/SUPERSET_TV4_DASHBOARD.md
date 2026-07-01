# Superset Dashboard - Tổng quan AdventureWorks

Dashboard đọc từ DataMart và audit, không truy vấn trực tiếp OLTP.

Dashboard được tổ chức thành ba tab: `Tổng quan`, `Sản phẩm` và `Khách hàng`.

URL:

`http://localhost:8088/superset/dashboard/adventureworks-tv4-executive-data-quality/`

## 1. Tab Tổng quan

Tám KPI đầu trang:

1. Tổng doanh thu.
2. Lợi nhuận gộp ước tính.
3. Tổng phí vận chuyển.
4. Tổng số khách hàng.
5. Tổng số lượng bán.
6. Biên lợi nhuận gộp ước tính.
7. Tổng số đơn hàng.
8. Giá trị bán dưới giá vốn.

Các giá trị tài chính dùng dữ liệu AdventureWorks và được trình bày theo USD.
`Profit` trong mẫu tham khảo được đổi thành `Lợi nhuận gộp ước tính` vì nguồn
không đủ chi phí để tính lợi nhuận ròng.

## 2. Tab Sản phẩm

1. Bar chart Top 10 sản phẩm theo doanh thu.
2. Donut chart cơ cấu doanh thu theo danh mục.
3. Bubble chart doanh thu, biên lợi nhuận và sản lượng sản phẩm.
4. Bar chart Top 10 sản phẩm gây lỗ gộp.

## 3. Tab Khách hàng

1. Bar chart Top 10 khách hàng theo doanh thu.
2. Heatmap doanh thu theo loại khách hàng và khu vực.
3. Horizontal bar doanh thu khách hàng theo khu vực.
4. Bar chart Top 10 khách hàng theo giá trị đơn hàng trung bình.

## 4. Phân tích trong tab Tổng quan

1. Doanh thu, giá vốn và lợi nhuận gộp theo tháng.
2. Xu hướng doanh thu theo tháng.
3. P&L gross-level gồm doanh thu, giá vốn, lợi nhuận gộp và giá trị bán dưới
   giá vốn.
4. Doanh thu theo quý, quốc gia và năm.

Biểu đồ thời gian loại tháng chưa hoàn chỉnh để tránh thể hiện sai xu hướng.

## 5. Chất lượng và đối soát

1. Source value, DW value, difference và reconciliation status.
2. Model, check name, failed record count và quality status.

Dashboard có tổng cộng 24 chart. Script bootstrap có thể chạy lặp lại để cập
nhật dashboard hiện tại mà không tạo chart trùng.
