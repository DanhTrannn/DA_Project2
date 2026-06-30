# TV4 Runbook - Data Platform and BI Integration

## Chạy phần TV4

```bash
./run_tv4.sh
```

Script khởi động PostgreSQL/dbt, chạy toàn bộ model và test, sau đó cập nhật
dashboard TV4 nếu Superset đang hoạt động.

Chạy lại dbt thủ công:

```bash
docker compose exec -T dbt dbt build \
  --project-dir /app/dbt \
  --profiles-dir /app/dbt
```

## Điều kiện đạt

- Tất cả dbt model/test PASS.
- `audit.source_to_dw_reconciliation` không có FAIL.
- `audit.data_quality_summary` không có FAIL.
- `mart_sales.executive_kpi` có đúng một dòng.
- Dashboard TV4 có đúng 9 chart.

## Kiểm tra nhanh

```bash
docker compose exec -T db psql -U postgres -d Adventureworks -P pager=off -c \
  "select * from audit.source_to_dw_reconciliation order by metric_name;"

docker compose exec -T db psql -U postgres -d Adventureworks -P pager=off -c \
  "select * from audit.data_quality_summary order by check_name;"

docker compose exec -T db psql -U postgres -d Adventureworks -P pager=off -c \
  "select * from mart_sales.executive_kpi;"
```

## Giới hạn

- COGS dùng `Product.StandardCost` nên gross profit là ước tính quản trị.
- Không trình bày net profit, debt, DSO/DPO hoặc cashflow như số liệu thật.
- TV4 kiểm chứng và tích hợp dữ liệu; ba model thuộc TV1-TV3.
