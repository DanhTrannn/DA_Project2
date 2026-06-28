import pandas as pd
import plotly.express as px
import streamlit as st
import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from aw_analytics.db import engine

# ============================
# Page Config
# ============================

st.set_page_config(
    page_title="Market Basket Analysis",
    page_icon="🛒",
    layout="wide"
)

st.title("🛒 Market Basket Analysis")
st.markdown(
"""
Association Rule Mining using **FP-Growth**.

Trang này dùng để trực quan hóa các product association rules được tạo ra từ các giao dịch bán hàng của AdventureWorks2022.
"""
)

# ============================
# Load Data
# ============================

db = engine()

rules = pd.read_sql("""
SELECT
    antecedents,
    consequents,
    support,
    confidence,
    lift,
    scored_at
FROM analytics.product_association_rules
""", db)

if rules.empty:
    st.warning("No association rules found.")
    st.stop()

product_summary = pd.read_sql("""
SELECT
    product_name,
    product_category_name,
    product_subcategory_name,
    quantity_sold,
    revenue,
    estimated_gross_profit
FROM mart_product.product_sales_summary
""", db)

if product_summary.empty:
    st.warning("No product summary data found.")
    st.stop()

# ============================
# KPI
# ============================

st.subheader("📦 Product Summary")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Products",
    product_summary["product_name"].nunique()
)

c2.metric(
    "Categories",
    product_summary["product_category_name"].nunique()
)

c3.metric(
    "Total Revenue",
    f"${product_summary['revenue'].sum():,.0f}"
)

c4.metric(
    "Total Gross Profit",
    f"${product_summary['estimated_gross_profit'].sum():,.0f}"
)

st.divider()

# ============================
# Filter
# ============================

st.sidebar.header("Filter Rules")

min_support = st.sidebar.slider(
    "Minimum Support",
    0.00,
    float(rules.support.max()),
    0.01,
    step=0.01
)

min_confidence = st.sidebar.slider(
    "Minimum Confidence",
    0.00,
    1.00,
    0.30,
    step=0.05
)

min_lift = st.sidebar.slider(
    "Minimum Lift",
    1.00,
    float(max(5.0, rules.lift.max())),
    1.20,
    step=0.10
)

filtered = rules[
    (rules.support >= min_support)
    &
    (rules.confidence >= min_confidence)
    &
    (rules.lift >= min_lift)
]

# ============================
# Chia Tabs
# ============================

tab_sales, tab_market, tab_recommend = st.tabs([
    "📊 Sales Overview",
    "🛒 Market Basket Analysis",
    "🎯 Product Recommendation"
])

with tab_sales:

# ============================
# Top 10 sản phẩm bán chạy nhất
# ============================

    st.subheader("🏆 Top 10 Selling Products")

    top_products = (
        product_summary
        .sort_values("quantity_sold", ascending=False)
        .head(10)
    )

    category_colors = {
        "Bikes": "#1f77b4",
        "Accessories": "#ff7f0e",
        "Clothing": "#2ca02c",
        "Components": "#d62728"
    }

    fig = px.bar(
        top_products,
        x="quantity_sold",
        y="product_name",
        orientation="h",
        text="quantity_sold",
        color="product_category_name",
        color_discrete_map=category_colors,
        labels={
            "quantity_sold": "Quantity Sold",
            "product_name": "Product Name",
            "product_category_name": "Category"
        }
    )

    fig.update_layout(
        legend_title="Category",
        yaxis=dict(categoryorder="total ascending")
    )

    st.plotly_chart(fig, use_container_width=True)

    best_product = top_products.iloc[0]

    st.success(
    f"""
    **Sản phẩm bán chạy nhất:** **{best_product.product_name}**

    Quantity Sold: {best_product.quantity_sold:,.0f} 
    """
    )

    st.info(
    """
    **Business Insight**

    **1. SẢN PHẨM QUỐC DÂN - AWC LOGO CAP**
    - Đây có thể là sản phẩm có mức giá dễ tiếp cận, dễ mua kèm hoặc là quà tặng/phụ kiện nhận diện thương hiệu phổ biến mà hầu như ai cũng mua khi đến cửa hàng.

    **2. MŨ BẢO HIỂM (Sport-100 Helmet) LÀ DÒNG SẢN PHẨM CỐT LÕI THEO COMBO**
    - Cả 3 phiên bản màu của Sport-100 Helmet (Blue: 6,743; Black: 6,532; Red: 6,266) đều lọt vào top 6 sản phẩm bán chạy nhất. Tổng lượng bán của riêng dòng mũ bảo hiểm này lên tới hơn 19,500.
    - Khách hàng có nhu cầu rất cao về vấn đề bảo hộ. 
    - Việc các màu sắc có lượng bán khá đồng đều cho thấy khách hàng mua theo sở thích cá nhân hoặc đây là sản phẩm thường mua kèm khi mua xe hoặc đồ thể thao.
    """
    )

    # ============================
    # Category bán chạy nhất
    # ============================

    st.subheader("📦 Quantity Sold by Category")

    category_sales = (
        product_summary
        .groupby("product_category_name", as_index=False)["quantity_sold"]
        .sum()
        .sort_values("quantity_sold", ascending=False)
    )

    category_colors = {
        "Bikes": "#1f77b4",
        "Accessories": "#ff7f0e",
        "Clothing": "#2ca02c",
        "Components": "#d62728"
    }

    fig = px.bar(
        category_sales,
        x="product_category_name",
        y="quantity_sold",
        color="product_category_name",
        color_discrete_map=category_colors,
        text="quantity_sold",
        labels={
            "quantity_sold": "Quantity Sold",
            "product_category_name": "Product Category"
        }
    )

    st.plotly_chart(fig, use_container_width=True)

    st.info(
    """
    **Business Insight**

    **1. BIKES LÀ ĐỘNG LỰC TĂNG TRƯỞNG CHÍNH**
    - Thông thường, phụ kiện (Accessories) hoặc quần áo (Clothing) bán ra số lượng sẽ nhiều hơn gấp nhiều lần so với xe đạp (Bikes) vì giá thành xe đạp cao hơn và tần suất thay thế thấp hơn. 
    - Tuy nhiên, biểu đồ trên lại cho thấy kết quả ngược lại, Bikes chiếm số lượng bán ra lớn nhất.
    - Bikes vừa là dòng sản phẩm cốt lõi mang lại doanh thu khổng lồ, vừa là dòng sản phẩm chính thu hút khách hàng.

    **2. CROSS-SELLING CHƯA ĐƯỢC KHAI THÁC TRIỆT ĐỂ**
    - Lượng bán của Clothing (73k) và Accessories (61k) đều thấp hơn lượng bán của Bikes (90k). 
    - Tỷ lệ lý tưởng phải là lượng phụ kiện và quần áo gấp nhiều lần lượng xe đạp bán ra do thông thường, một khách hàng mua xe đạp sẽ có nhu cầu mua kèm ít nhất 1–2 món phụ kiện (mũ bảo hiểm, bình nước, khóa xe) hoặc đồ bảo hộ (áo jersey, quần short đạp xe).
    - Doanh nghiệp có thể đang bỏ lỡ cross-sell rất lớn. 
    - Khách hàng mua xe đạp xong có thể đang sang các thương hiệu khác để mua phụ kiện/quần áo, hoặc các gói combo bán kèm chưa đủ hấp dẫn.
    """
    )

    # ============================
    # Revenue & Gross Profit by Category
    # ============================

    st.subheader("💰 Revenue & Gross Profit by Category")

    category_summary = (
        product_summary
        .groupby("product_category_name", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            estimated_gross_profit=("estimated_gross_profit", "sum")
        )
        .sort_values("revenue", ascending=False)
    )

    fig = px.bar(
        category_summary,
        x="product_category_name",
        y=["revenue", "estimated_gross_profit"],
        barmode="group",
        text_auto=".2s",
        labels={
            "value": "Amount",
            "product_category_name": "Product Category",
            "variable": "Metric"
        }
    )

    fig.update_layout(
        legend_title_text="Metric",
        xaxis_title="Product Category",
        yaxis_title="Amount"
    )

    st.plotly_chart(fig, use_container_width=True)

    best_revenue = category_summary.loc[category_summary["revenue"].idxmax()]

    best_profit = category_summary.loc[category_summary["estimated_gross_profit"].idxmax()]

    col1, col2 = st.columns(2)

    with col1:
        st.success(
            f"""
    **Highest Revenue Category**

    **{best_revenue.product_category_name}**

    Revenue: **{best_revenue.revenue:,.0f}**
    """
        )

    with col2:
        st.success(
            f"""
    **Highest Gross Profit Category**

    **{best_profit.product_category_name}**

    Gross Profit: **{best_profit.estimated_gross_profit:,.0f}**
    """
        )

    st.info(
    """
    **Business Insight**

    **1. SỰ PHỤ THUỘC QUÁ LỚN VÀO BIKES**
    - Bikes chiếm hơn 85% tổng doanh thu và gần như toàn bộ lợi nhuận.
    Các category khác đóng góp rất nhỏ về doanh thu.
    - Doanh nghiệp đang rất rủi ro nếu có biến động trên phân khúc xe đạp (cạnh tranh, chuỗi cung ứng, xu hướng thị trường).
    - Giải pháp: Giảm rủi ro bằng cách đẩy mạnh cross-sell từ Bikes sang các category khác (đặc biệt Accessories & Clothing).

    **2. COMPONENTS LÀ ĐIỂM YẾU**
    - Doanh thu khá (12M) nhưng Gross Profit rất thấp (chỉ 490k).
    - Components đang không hiệu quả về mặt lợi nhuận (có thể do chi phí nhập hàng cao hoặc giá bán cạnh tranh).
    - Giải pháp: Xem xét lại giá vốn (COGS) và chiến lược giá của Components.
    """
    )

with tab_market:
    # ============================
    # Frequently Bought Together
    # ============================

    st.subheader("📋 Frequently Bought Together")

    st.dataframe(
        filtered.sort_values(
            ["lift", "confidence"],
            ascending=False
        ),
        use_container_width=True
    )

    # ============================
    # Network Graph – Frequently Bought Together
    # ============================

    st.subheader("🌐 Frequently Bought Together Network")

    G = nx.DiGraph()

    top_rules = (
        filtered
        .sort_values(["lift", "confidence"], ascending=False)
        .head(40)
    )

    for _, row in top_rules.iterrows():

        G.add_edge(
            row["antecedents"],
            row["consequents"],
            lift=row["lift"],
            confidence=row["confidence"]
        )

    pos = nx.spring_layout(
        G,
        k=1.2,
        seed=42
    )

    edge_x = []
    edge_y = []

    for u, v in G.edges():

        x0, y0 = pos[u]
        x1, y1 = pos[v]

        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(width=1.5, color="lightgray"),
        hoverinfo="none"
    )

    node_x = []
    node_y = []
    hover_text = []
    node_size = []

    for node in G.nodes():

        x, y = pos[node]

        node_x.append(x)
        node_y.append(y)
        degree = G.degree(node)

        node_size.append(12 + degree * 3)

        hover_text.append(
            f"<b>{node}</b><br>"
            f"Connections: {degree}"
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",       
        hoverinfo="text",
        hovertext=hover_text,
        marker=dict(
            size=node_size,
            color=node_size,
            colorscale="Blues",
            showscale=True,
            colorbar=dict(
                title="Degree"
            ),
            line=dict(width=1, color="black")
        )
    )


    fig = go.Figure(data=[edge_trace, node_trace])

    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        height=700,
        margin=dict(l=20, r=20, t=20, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ============================
    # Scatter Plot
    # ============================

    st.subheader("📈 Support vs Confidence")

    fig = px.scatter(
        filtered,
        x="support",
        y="confidence",
        color="lift",
        size="lift",
        hover_name="antecedents",
        hover_data=[
            "consequents",
            "support",
            "confidence",
            "lift"
        ]
    )

    st.plotly_chart(fig, use_container_width=True)

    # ============================
    # Top 10 Rules
    # ============================

    st.subheader("🏆 Top 10 Strongest Association Rules")

    top10 = (
        filtered
        .sort_values(
            ["lift", "confidence"],
            ascending=False
        )
        .head(10)
    )

    st.table(
        top10[
            [
                "antecedents",
                "consequents",
                "support",
                "confidence",
                "lift"
            ]
        ]
    )

with tab_recommend:

# ============================
# Cross-selling Recommendation
# ============================

    st.subheader("🎯 Cross-selling Recommendations")

    recommendations = (
        filtered
        .sort_values(
            ["lift", "confidence"],
            ascending=False
        )
        .head(5)
    )

    for _, row in recommendations.iterrows():

        st.success(f"""
    Nếu khách hàng mua

    **{row['antecedents']}**

    thì có khả năng cao họ cũng sẽ mua

    **{row['consequents']}**

    Support : {row['support']:.2f}

    Confidence : {row['confidence']:.2f}

    Lift : {row['lift']:.2f}

    👉 Recommendation:

    Đưa ra các ưu đãi giảm giá khi mua kèm sản phẩm hoặc hiển thị **{row['consequents']}** như một đề xuất khi khách hàng mua **{row['antecedents']}**.
    """)

    # ============================
    # Recommendation System
    # ============================

    st.divider()
    st.subheader("🛍 Product Recommendation")

    # Lấy toàn bộ sản phẩm xuất hiện ở antecedents
    products = sorted({
        item.strip()
        for row in rules["antecedents"]
        for item in row.split(" + ")
    })

    selected_product = st.selectbox(
        "Select a product",
        products
    )

    # Các rule chứa sản phẩm đã chọn
    recommend = filtered[
        filtered["antecedents"].str.contains(
            selected_product,
            case=False,
            na=False
        )
    ].copy()

    if recommend.empty:
        st.info("No recommendation found.")
    else:

        recommend = recommend.sort_values(
            ["lift", "confidence", "support"],
            ascending=False
        )

        st.success(
            f"Found {len(recommend)} recommendation rule(s) for **{selected_product}**."
        )

        # Hiển thị bảng rule
        st.dataframe(
            recommend[
                [
                    "antecedents",
                    "consequents",
                    "support",
                    "confidence",
                    "lift"
                ]
            ],
            use_container_width=True
        )

        st.markdown("### 🎯 Top Recommended Products")

        # Gom theo consequent để tránh trùng
        top_products = (
            recommend.groupby("consequents")
            .agg(
                confidence=("confidence", "max"),
                lift=("lift", "max"),
                support=("support", "max")
            )
            .reset_index()
            .sort_values(
                ["lift", "confidence"],
                ascending=False
            )
        )

        for _, row in top_products.head(5).iterrows():

            st.markdown(
                f"""
    **🛒 {row['consequents']}**

    - Confidence : **{row['confidence']:.2f}**
    - Lift : **{row['lift']:.2f}**
    - Support : **{row['support']:.3f}**
    """
            )