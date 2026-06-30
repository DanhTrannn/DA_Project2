# Superset Dashboard Spec - TV4

Dashboard TV4 đọc từ DataMart và audit, không đọc trực tiếp OLTP.

URL:

`http://localhost:8088/superset/dashboard/adventureworks-tv4-executive-data-quality/`

## 1. Tổng quan điều hành

Dataset: `mart_sales.executive_kpi`.

1. Tổng doanh thu.
2. Lợi nhuận gộp ước tính.
3. Biên lợi nhuận gộp ước tính.
4. Tổng số đơn hàng.
5. Giá trị bán dưới giá vốn.

## 2. Hiệu quả tài chính

Dataset:

- `mart_sales.sales_monthly_kpi`.
- `mart_finance.management_pnl_summary`.

Charts:

1. Doanh thu và lợi nhuận gộp theo tháng.
2. Gross-level P&L gồm revenue, estimated COGS, estimated gross profit và
   loss amount.

## 3. Chất lượng và đối soát

Dataset:

- `audit.source_to_dw_reconciliation`.
- `audit.data_quality_summary`.

Charts:

1. Source value, DW value, difference và reconciliation status.
2. Model, check name, failed record count và quality status.

Dashboard có tổng cộng 9 chart. Bootstrap phải chạy lặp được mà không tạo
chart trùng.
