# Superset TV2 - Hiệu quả sản phẩm

Dashboard được tổ chức theo luồng kể chuyện dữ liệu, đi từ kết luận chính đến
bằng chứng và hành động:

1. **Quy mô có đi cùng hiệu quả không?** Revenue, estimated gross profit,
   margin và số sản phẩm đang lỗ.
2. **Doanh thu tập trung ở đâu?** Đối chiếu revenue và margin theo category.
3. **Sản phẩm nào dẫn đầu và sản phẩm nào làm thất thoát lợi nhuận?** Top
   revenue đặt cạnh danh sách sản phẩm lỗ nặng nhất.
4. **Nên ưu tiên sản phẩm nào?** Ma trận profitability đối chiếu revenue,
   margin và quantity.

Thông điệp chính hiển thị ngay trên tiêu đề chart:

- Bikes tạo 86,2% doanh thu nhưng estimated gross margin toàn danh mục chỉ 8,5%.
- 56 sản phẩm làm giảm estimated gross profit khoảng 1,33 triệu USD.
- Accessories có estimated margin khoảng 50% nhưng mới chiếm 1,2% doanh thu.
- Cần rà soát giá bán/chi phí của nhóm bike đang lỗ và thử mở rộng nhóm
  accessories có biên cao.

Các con số và khoảng thời gian trong tiêu đề được bootstrap đọc trực tiếp từ
DataMart, vì vậy chạy lại pipeline sẽ cập nhật phần kể chuyện theo dữ liệu mới.

## Nguyên tắc trực quan hóa

- Hiển thị trực tiếp KPI thay vì dùng biểu đồ cho một con số đơn lẻ.
- Dùng cột ngang, sắp xếp giảm dần cho tên category/sản phẩm dài.
- Không dùng biểu đồ tròn, vùng hoặc trục Y thứ cấp vì khó so sánh chính xác.
- Dùng tiêu đề dạng kết luận để người xem hiểu insight trước khi đọc chi tiết.
- Giảm số metric trên mỗi chart và đặt chart rủi ro cạnh chart tăng trưởng để
  người xem nhận ra trade-off.

Thiết kế dựa trên nội dung trong `Kể chuyển bằng dữ liệu.pptx`. Bài tổng hợp
[Apache Superset alternatives](https://trevor.io/blog/apache-superset-alternatives)
được dùng để đối chiếu tiêu chí self-service: dashboard phải tiếp cận được với
người không viết SQL, không dùng để thay đổi nền tảng khỏi Superset.

## Nguồn dữ liệu

- Dataset Superset: `mart_product.product_sales_summary`.
- Grain: một dòng cho mỗi sản phẩm.
- Gross profit và gross margin là giá trị ước tính từ `StandardCost`, không
  phải lợi nhuận kế toán thực tế.

## Các chart

| Biểu đồ | Câu hỏi được trả lời |
|---|---|
| Doanh thu | Quy mô doanh thu sản phẩm là bao nhiêu? |
| Lợi nhuận gộp ước tính | Lợi nhuận gộp ước tính là bao nhiêu? |
| Biên lợi nhuận gộp ước tính | Hiệu quả chung có tương xứng với quy mô? |
| Sản phẩm đang lỗ | Danh mục có bao nhiêu sản phẩm đang lỗ? |
| Doanh thu theo danh mục | Doanh thu tập trung ở danh mục nào? |
| Biên lợi nhuận theo danh mục | Danh mục nào có dư địa mở rộng? |
| Top sản phẩm theo doanh thu | Sản phẩm nào dẫn đầu doanh thu? |
| Top sản phẩm theo số lượng | Sản phẩm nào bán được nhiều nhất? |
| Top sản phẩm theo lợi nhuận gộp | Sản phẩm nào đóng góp lợi nhuận cao nhất? |
| Thất thoát lợi nhuận | Sản phẩm nào cần xử lý trước? Bảng này được mở rộng chiều dọc để hiển thị rõ danh sách sản phẩm lỗ. |
| Ma trận hiệu quả sản phẩm | Sản phẩm nào nên được ưu tiên? |

Profitability matrix được đọc như sau:

- Trục X: revenue.
- Trục Y: estimated gross margin.
- Kích thước bubble: quantity sold.
- Màu bubble: product category.

Sản phẩm ở phía trên bên phải vừa có doanh thu cao vừa có biên lợi nhuận tốt.
Sản phẩm có doanh thu cao nhưng nằm thấp cần được xem lại giá bán hoặc chi phí.

## Chạy toàn bộ

Từ thư mục gốc project:

```bash
./run_full_pipeline.sh
```

Script sẽ build DataMart, chạy ba model, tạo dashboard TV4 và dashboard TV2.

## Chỉ tạo lại dashboard TV2

Khi DataMart đã tồn tại:

```bash
docker compose up -d --build superset
docker compose exec -T superset python /app/bootstrap/bootstrap_tv2.py
```

Bootstrap có tính idempotent: chạy lại sẽ cập nhật dashboard/chart hiện tại,
đồng thời đổi tên các chart TV2 cũ sang tiêu đề insight mới thay vì tạo bản sao.

## Cách xem

1. Mở `http://localhost:8088`.
2. Đăng nhập bằng `admin` / `admin`, trừ khi đã đổi trong biến môi trường.
3. Chọn **Dashboards**.
4. Mở **Hiệu quả sản phẩm AdventureWorks - Doanh thu và rủi ro lợi nhuận**.

Truy cập trực tiếp:

```text
http://localhost:8088/superset/dashboard/adventureworks-tv2-product-analytics/
```

Kết quả association rules và recommendation không nằm trong dashboard này và
vẫn được trình bày tại Streamlit:

```text
http://localhost:8501
```
