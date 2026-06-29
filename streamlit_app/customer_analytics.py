import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

DB_URL = "postgresql+psycopg2://postgres:postgres@db:5432/Adventureworks"

st.set_page_config(page_title="TV1 - Customer Analytics", layout="wide")

@st.cache_data
def load_data():
    engine = create_engine(DB_URL)
    
    segment = pd.read_sql("select * from analytics.customer_segment", engine)
    summary = pd.read_sql("select * from analytics.customer_segment_summary", engine)
    metrics = pd.read_sql("select * from analytics.customer_segmentation_metrics order by k", engine)
    top_value = pd.read_sql("select * from analytics.customer_top_value", engine)
    eda = pd.read_sql("select * from analytics.customer_eda_summary", engine)

    return segment, summary, metrics, top_value, eda

segment, summary, metrics, top_value, eda = load_data()

st.title("TV1 - Customer Analytics: RFM + K-Means")

st.write(
    """
    Dashboard này trình bày kết quả phân khúc khách hàng bằng RFM và K-Means.
    Các segment được dùng để xác định nhóm khách hàng giá trị cao, khách hàng trung thành,
    khách hàng có nguy cơ rời bỏ và nhóm khách cần phát triển thêm.
    """
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Customers", f"{len(segment):,}")
col2.metric("Total Revenue", f"{summary['total_revenue'].sum():,.0f}")
col3.metric("Gross Profit", f"{summary['total_gross_profit'].sum():,.0f}")
col4.metric("Silhouette", f"{segment['silhouette_score'].iloc[0]:.4f}")

st.subheader("EDA & Preprocessing Summary")

st.write(
    """
    Trước khi chạy K-Means, nhóm kiểm tra missing values, thống kê mô tả và độ lệch phân phối.
    Các biến monetary và average order value thường bị lệch phải, nên mô hình áp dụng log1p
    trước khi chuẩn hóa bằng StandardScaler.
    """
)

st.dataframe(
    eda.rename(
        columns={
            "feature": "Feature",
            "missing_values": "Missing Values",
            "mean": "Mean",
            "std": "Std",
            "min": "Min",
            "median": "Median",
            "max": "Max",
            "skewness_before_log": "Skewness Before Log",
            "skewness_after_log": "Skewness After Log",
        }
    ),
    use_container_width=True,
)

col_before, col_after = st.columns(2)

with col_before:
    st.write("**Skewness Before Log**")
    st.bar_chart(
        eda.set_index("feature")["skewness_before_log"]
    )

with col_after:
    st.write("**Skewness After Log**")
    st.bar_chart(
        eda.set_index("feature")["skewness_after_log"]
    )

st.info("""
EDA Summary

• Không có giá trị thiếu (Missing Values = 0) ở tất cả các feature.

• Monetary và Average Order Value có độ lệch phải (right-skewed) rất lớn
(skewness > 10), cho thấy chỉ một số ít khách hàng tạo doanh thu rất cao.

• Sau khi áp dụng log1p:
    - Monetary: 12.80 → 0.14
    - Average Order Value: 10.81 → -0.05

=> Dữ liệu trở nên cân bằng hơn trước khi StandardScaler và K-Means.
""")

st.subheader("1. Segment Distribution")
segment_count = summary[["segment_name", "customer_count"]].sort_values(
    "customer_count", ascending=False
)
st.bar_chart(segment_count.set_index("segment_name"))

st.subheader("2. Revenue and Gross Profit by Segment")
revenue_chart = summary[
    ["segment_name", "total_revenue", "total_gross_profit"]
].set_index("segment_name")
st.bar_chart(revenue_chart)

st.subheader("3. Scatter: Frequency vs Monetary")
st.scatter_chart(
    segment,
    x="frequency",
    y="monetary",
    color="segment_name",
)

st.subheader("4. Top High Value Customers")
high_value = top_value[top_value["segment_name"] == "high_value"].sort_values(
    "revenue", ascending=False
)
st.dataframe(
    high_value[
        [
            "customer_name",
            "territory_name",
            "revenue",
            "estimated_gross_profit",
            "estimated_gross_margin_pct",
            "recency_days",
            "frequency",
        ]
    ].head(15),
    use_container_width=True,
)

st.subheader("5. At Risk Customers")
at_risk = top_value[top_value["segment_name"] == "at_risk"].sort_values(
    "recency_days", ascending=False
)
st.dataframe(
    at_risk[
        [
            "customer_name",
            "territory_name",
            "revenue",
            "estimated_gross_profit",
            "recency_days",
            "frequency",
            "average_order_value",
        ]
    ].head(15),
    use_container_width=True,
)

st.subheader("6. Segment Profiles")

segment_desc = {
    "high_value": "Nhóm khách hàng có tổng giá trị mua cao nhất. Đây là nhóm VIP cần ưu tiên giữ chân.",
    "loyal": "Nhóm mua thường xuyên nhất. Phù hợp để triển khai loyalty program, bundle và cross-sell.",
    "at_risk": "Nhóm đã lâu không quay lại mua hàng. Cần chiến dịch win-back hoặc voucher quay lại.",
    "developing": "Nhóm đông, mua gần đây nhưng giá trị còn thấp. Có tiềm năng upsell và phát triển.",
    "low_value": "Nhóm có giá trị và tần suất mua thấp. Nên chăm sóc bằng automation marketing.",
}

segment_reco = {
    "high_value": "VIP care, ưu đãi riêng, chăm sóc cá nhân hóa.",
    "loyal": "Cross-sell, bundle sản phẩm, loyalty points.",
    "at_risk": "Email remarketing, voucher quay lại, win-back campaign.",
    "developing": "Welcome campaign, gợi ý sản phẩm, ưu đãi lần mua tiếp theo.",
    "low_value": "Marketing tự động, ưu đãi chi phí thấp, không ưu tiên chăm sóc thủ công.",
}

profile = summary[
    [
        "segment_name",
        "customer_count",
        "total_revenue",
        "total_gross_profit",
        "avg_recency",
        "avg_frequency",
        "avg_monetary",
        "avg_order_value",
    ]
].copy()

profile["business_meaning"] = profile["segment_name"].map(segment_desc)
profile["recommendation"] = profile["segment_name"].map(segment_reco)

profile = profile.sort_values("total_revenue", ascending=False)

st.dataframe(
    profile.rename(
        columns={
            "segment_name": "Segment",
            "customer_count": "Customers",
            "total_revenue": "Total Revenue",
            "total_gross_profit": "Total Gross Profit",
            "avg_recency": "Avg Recency Days",
            "avg_frequency": "Avg Frequency",
            "avg_monetary": "Avg Monetary",
            "avg_order_value": "Avg Order Value",
            "business_meaning": "Business Meaning",
            "recommendation": "Recommendation",
        }
    ),
    use_container_width=True,
)

st.subheader("7. K-Means Evaluation")

st.dataframe(metrics, use_container_width=True)

selected_k = int(segment["selected_k"].iloc[0])
silhouette = float(segment["silhouette_score"].iloc[0])

st.markdown(
    f"""
    **Selected k:** {selected_k}  
    **Silhouette score:** {silhouette:.4f}

    K-Means được đánh giá với k từ 3 đến 6 trên dữ liệu đã tiền xử lý
    bằng **log1p transformation** và **StandardScaler**.

    Kết quả cho thấy **k = 5** đạt silhouette score cao nhất trong các giá trị đã thử.
    Vì vậy, nhóm chọn **k = 5** cho mô hình cuối cùng. Số cụm này cũng phù hợp để diễn giải
    thành các nhóm khách hàng: **High Value, Loyal, At Risk, Developing và Low Value**.
    """
)

st.subheader("8. Insight & Recommendation")

total_customers = summary["customer_count"].sum()
total_revenue = summary["total_revenue"].sum()

def get_segment_row(name):
    return summary[summary["segment_name"] == name].iloc[0]

high = get_segment_row("high_value")
loyal = get_segment_row("loyal")
risk = get_segment_row("at_risk")
developing = get_segment_row("developing")
low = get_segment_row("low_value")

st.markdown(
    f"""
    **Insight 1 - High Value customers:**  
    Nhóm **High Value** chỉ có **{int(high['customer_count']):,} khách hàng**
    ({high['customer_count'] / total_customers:.1%} tổng khách hàng) nhưng tạo khoảng
    **{high['total_revenue']:,.0f} doanh thu** ({high['total_revenue'] / total_revenue:.1%} tổng doanh thu).
    Đây là nhóm cần được ưu tiên giữ chân bằng chương trình VIP, ưu đãi riêng và chăm sóc cá nhân hóa.

    **Insight 2 - Loyal customers:**  
    Nhóm **Loyal** có tần suất mua trung bình khoảng **{loyal['avg_frequency']:.2f} đơn/khách**,
    cao nhất trong các nhóm. Nhóm này phù hợp để triển khai **cross-sell, bundle sản phẩm**
    và loyalty points nhằm tăng giá trị đơn hàng.

    **Insight 3 - At Risk customers:**  
    Nhóm **At Risk** có recency trung bình khoảng **{risk['avg_recency']:.0f} ngày**,
    cho thấy họ đã lâu không quay lại. Doanh nghiệp nên triển khai **win-back campaign**,
    email remarketing hoặc voucher quay lại.

    **Insight 4 - Developing customers:**  
    Nhóm **Developing** là nhóm đông nhất với **{int(developing['customer_count']):,} khách hàng**.
    Họ có hành vi mua gần đây nhưng giá trị đơn hàng còn thấp, nên có thể phát triển bằng
    gợi ý sản phẩm, ưu đãi lần mua tiếp theo và chương trình loyalty cơ bản.

    **Insight 5 - Low Value customers:**  
    Nhóm **Low Value** có monetary và frequency thấp. Doanh nghiệp không nên đầu tư chăm sóc thủ công quá nhiều,
    mà nên dùng automation marketing và ưu đãi chi phí thấp.
    """
)