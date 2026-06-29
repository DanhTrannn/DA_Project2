import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine

st.set_page_config(page_title="TV3 Sales Intelligence", layout="wide")

# 1. Database connection
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "15432")
DB_NAME = os.getenv("SOURCE_DATABASE", "Adventureworks")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)

with st.sidebar:
    st.caption("Database")
    st.code(DB_URL.replace(DB_PASSWORD, "***"))


# 2. Format helpers
def money(x):
    if pd.isna(x):
        return "N/A"
    return f"${float(x):,.0f}"


def md_money(x):
    # Dùng trong st.markdown để ký tự $ không bị hiểu nhầm là công thức LaTeX
    return money(x).replace("$", "\\$")


def pct(x):
    if pd.isna(x):
        return "N/A"
    return f"{float(x):.1%}"


def pct_from_100(x):
    if pd.isna(x):
        return "N/A"
    return f"{float(x):.1f}%"


def number(x):
    if pd.isna(x):
        return "N/A"
    return f"{float(x):,.0f}"


def safe_float(x, default=0.0):
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


# 3. Load data

@st.cache_data(ttl=300)
def read_sql(query):
    return pd.read_sql(query, engine)


@st.cache_data(ttl=300)
def load_all():
    actual = read_sql("""
        select
            month,
            order_count,
            quantity_sold,
            revenue,
            estimated_cogs,
            estimated_gross_profit,
            estimated_gross_margin_pct
        from mart_sales_forecast.monthly_sales_series
        order by month
    """)

    actual.columns = [c.lower() for c in actual.columns]
    actual = actual.rename(columns={
        "month": "month_start",
        "estimated_gross_profit": "gross_profit",
        "estimated_gross_margin_pct": "gross_margin"
    })

    actual["month_start"] = pd.to_datetime(actual["month_start"])

    for col in ["order_count", "quantity_sold", "revenue", "estimated_cogs", "gross_profit", "gross_margin"]:
        actual[col] = pd.to_numeric(actual[col], errors="coerce")

    forecast = read_sql("""
        select *
        from analytics.sales_forecast
        order by month_start
    """)

    metrics = read_sql("""
        select *
        from analytics.sales_forecast_metric
        order by model_rank
    """)

    decomp = read_sql("""
        select *
        from analytics.sales_forecast_decomposition
        order by month_start
    """)

    scenario = read_sql("""
        select *
        from analytics.sales_forecast_scenario
        order by month_start
    """)

    summary = read_sql("""
        select *
        from analytics.sales_forecast_summary
    """)

    for df in [forecast, decomp, scenario]:
        if not df.empty and "month_start" in df.columns:
            df["month_start"] = pd.to_datetime(df["month_start"])

    if not summary.empty:
        for col in ["current_month", "next_month"]:
            if col in summary.columns:
                summary[col] = pd.to_datetime(summary[col])

    return actual, forecast, metrics, decomp, scenario, summary


# 4. Insight helpers

def build_eda_insights(actual):
    valid = actual.dropna(subset=["revenue"]).copy()
    if valid.empty:
        return ["Chưa đủ dữ liệu để nhận xét EDA."]

    first = valid.iloc[0]
    last = valid.iloc[-1]
    prev = valid.iloc[-2] if len(valid) >= 2 else None

    revenue_change = safe_float(last["revenue"]) / safe_float(first["revenue"], 1) - 1
    order_change = safe_float(last["order_count"]) / safe_float(first["order_count"], 1) - 1
    quantity_change = safe_float(last["quantity_sold"]) / safe_float(first["quantity_sold"], 1) - 1

    recent_margin = valid["gross_margin"].tail(6).mean()
    overall_margin = valid["gross_margin"].mean()

    insights = []
    insights.append(
        f"EDA dùng **{len(valid)} tháng hoàn chỉnh**, từ **{first['month_start'].date()}** đến **{last['month_start'].date()}**."
    )
    insights.append(
        f"Doanh thu tăng từ {md_money(first['revenue'])} lên {md_money(last['revenue'])} "
        f"({pct(revenue_change)}), cho thấy xu hướng dài hạn đi lên nhưng vẫn dao động mạnh theo tháng."
    )
    insights.append(
        f"Order count tăng {pct(order_change)}, quantity sold tăng {pct(quantity_change)}; "
        "doanh thu vì vậy chịu ảnh hưởng rõ từ volume bán hàng."
    )

    if prev is not None:
        mom = safe_float(last["revenue"]) / safe_float(prev["revenue"], 1) - 1
        if abs(mom) > 0.3:
            insights.append(
                f"Tháng gần nhất ({last['month_start'].strftime('%Y-%m')}) thay đổi {pct(mom)} so với tháng trước, "
                "nên forecast cần được xem là tín hiệu tham khảo."
            )

    if pd.notna(recent_margin) and pd.notna(overall_margin):
        insights.append(
            f"Gross margin 6 tháng gần nhất là {pct(recent_margin)}, so với trung bình toàn kỳ {pct(overall_margin)}."
        )

    return insights

def prepare_eda_features(actual_eda):
    """Tạo thêm các cột EDA từ bảng monthly_sales_series."""
    df = actual_eda.copy().sort_values("month_start")
    df["year"] = df["month_start"].dt.year
    df["quarter"] = df["month_start"].dt.to_period("Q").astype(str)
    df["month_no"] = df["month_start"].dt.month
    df["month_name"] = df["month_start"].dt.strftime("%b")

    df["revenue_diff"] = df["revenue"].diff()
    df["mom_growth"] = df["revenue"].pct_change()
    df["yoy_growth"] = df["revenue"].pct_change(12)

    df["aov"] = df["revenue"] / df["order_count"].replace(0, pd.NA)
    df["avg_price_per_unit"] = df["revenue"] / df["quantity_sold"].replace(0, pd.NA)

    return df


def build_growth_insight(df):
    if df.empty or len(df) < 2:
        return "Chưa đủ dữ liệu để phân tích tăng trưởng."

    valid_mom = df.dropna(subset=["mom_growth"])
    if valid_mom.empty:
        return "Chưa đủ dữ liệu để tính MoM Growth."

    best_mom = valid_mom.loc[valid_mom["mom_growth"].idxmax()]
    worst_mom = valid_mom.loc[valid_mom["mom_growth"].idxmin()]

    text = (
        f"MoM tăng mạnh nhất ở **{best_mom['month_start'].strftime('%Y-%m')}** ({pct(best_mom['mom_growth'])}); "
        f"giảm mạnh nhất ở **{worst_mom['month_start'].strftime('%Y-%m')}** ({pct(worst_mom['mom_growth'])})."
    )

    valid_yoy = df.dropna(subset=["yoy_growth"])
    if not valid_yoy.empty:
        latest_yoy = valid_yoy.iloc[-1]
        text += f" YoY gần nhất: **{latest_yoy['month_start'].strftime('%Y-%m')} = {pct(latest_yoy['yoy_growth'])}**."

    return text

def build_profit_insight(df):
    if df.empty:
        return "Chưa đủ dữ liệu để phân tích lợi nhuận."

    total_revenue = df["revenue"].sum()
    total_profit = df["gross_profit"].sum()
    avg_margin = df["gross_margin"].mean()
    recent_margin = df["gross_margin"].tail(6).mean()

    return (
        f"Gross profit toàn kỳ đạt {md_money(total_profit)} trên revenue {md_money(total_revenue)}. "
        f"Gross margin trung bình là **{pct(avg_margin)}**, 6 tháng gần nhất là **{pct(recent_margin)}**; "
        "vì vậy cần xem cả revenue và margin khi đánh giá hiệu quả bán hàng."
    )

def build_driver_insight(df):
    if df.empty or len(df) < 2:
        return "Chưa đủ dữ liệu để phân tích động lực doanh thu."

    first = df.iloc[0]
    last = df.iloc[-1]

    rev_change = safe_float(last["revenue"]) / safe_float(first["revenue"], 1) - 1
    order_change = safe_float(last["order_count"]) / safe_float(first["order_count"], 1) - 1
    qty_change = safe_float(last["quantity_sold"]) / safe_float(first["quantity_sold"], 1) - 1
    aov_change = safe_float(last["aov"]) / safe_float(first["aov"], 1) - 1

    return (
        f"Revenue tăng **{pct(rev_change)}** trong toàn kỳ. Order count tăng **{pct(order_change)}**, "
        f"quantity sold tăng **{pct(qty_change)}**, trong khi AOV thay đổi **{pct(aov_change)}**. "
        "Điều này gợi ý doanh thu tăng chủ yếu nhờ mở rộng số đơn/volume, nhưng giá trị trung bình mỗi đơn có xu hướng giảm."
    )

def build_time_level_insight(df):
    if df.empty:
        return "Chưa đủ dữ liệu để nhận xét theo thời gian."

    year_sum = df.groupby("year", as_index=False)["revenue"].sum()
    best_year = year_sum.loc[year_sum["revenue"].idxmax()]

    quarter_sum = df.groupby("quarter", as_index=False)["revenue"].sum()
    best_quarter = quarter_sum.loc[quarter_sum["revenue"].idxmax()]

    best_month = df.loc[df["revenue"].idxmax()]

    return (
        f"Doanh thu có xu hướng tăng đến năm 2024. "
        f"Năm cao nhất: **{int(best_year['year'])}** ({md_money(best_year['revenue'])}); "
        f"quý cao nhất: **{best_quarter['quarter']}** ({md_money(best_quarter['revenue'])}); "
        f"tháng cao nhất: **{best_month['month_start'].strftime('%Y-%m')}** ({md_money(best_month['revenue'])})."
    )

def build_model_ranking_insight(metrics):
    if metrics.empty:
        return "Chưa có dữ liệu metric để nhận xét."

    best = metrics.iloc[0]
    second = metrics.iloc[1] if len(metrics) > 1 else None

    text = (
        f"**{best['model_name']}** có WAPE thấp nhất (**{pct(best['wape'])}**) "
        "trong các mô hình được thử nghiệm, nên được chọn làm mô hình hiện tại. "
        "WAPE càng thấp thì sai số tương đối càng nhỏ."
    )

    if second is not None:
        gap = safe_float(second["wape"]) - safe_float(best["wape"])
        text += (
            f" Chênh lệch với mô hình hạng 2 là **{pct(gap)}**, "
            "cho thấy các mô hình top đầu có kết quả khá gần nhau."
        )

    text += (
        " Vì dữ liệu chỉ có khoảng vài chục tháng, kết quả nên được dùng để so sánh mô hình "
        "và hỗ trợ lập kế hoạch ngắn hạn, không nên diễn giải như dự báo chắc chắn tuyệt đối."
    )

    return text


def build_forecast_insight(test_df, future_df, model, metrics):
    parts = []

    if not test_df.empty:
        tmp = test_df.dropna(subset=["actual_revenue", "forecast_revenue"]).copy()
        if not tmp.empty:
            tmp["abs_error"] = (tmp["actual_revenue"] - tmp["forecast_revenue"]).abs()
            worst = tmp.loc[tmp["abs_error"].idxmax()]
            parts.append(
                f"Trong tập test, sai lệch lớn nhất nằm ở tháng {worst['month_start'].date()} "
                f"với actual {md_money(worst['actual_revenue'])} và forecast {md_money(worst['forecast_revenue'])}."
            )

    metric_row = metrics[metrics["model_name"] == model]
    if not metric_row.empty:
        wape_val = metric_row.iloc[0]["wape"]
        parts.append(
            f"Mô hình **{model}** có WAPE {pct(wape_val)}, tức sai số tương đối trên tập test còn khoảng {pct(wape_val)}."
        )

    if not future_df.empty:
        first_future = future_df.iloc[0]
        last_future = future_df.iloc[-1]
        parts.append(
            f"Giai đoạn forecast tương lai dao động từ {md_money(first_future['forecast_revenue'])} "
            f"đến {md_money(last_future['forecast_revenue'])}. Kết quả này phản ánh xu hướng theo mô hình hiện tại "
            "và nên được cập nhật khi có dữ liệu thực tế mới."
        )

    return " ".join(parts) if parts else "Chưa đủ dữ liệu để nhận xét forecast."


def build_decomposition_insight(decomp):
    if decomp.empty:
        return "Chưa đủ dữ liệu để decomposition."

    trend = decomp["trend"].dropna()
    if trend.empty:
        return "Chưa đủ dữ liệu trend để nhận xét decomposition."

    trend_start = trend.iloc[0]
    trend_end = trend.iloc[-1]
    trend_growth = safe_float(trend_end) / safe_float(trend_start, 1) - 1

    seasonal_amp = decomp["seasonal"].max() - decomp["seasonal"].min()
    residual_max_idx = decomp["residual"].abs().idxmax()
    residual_row = decomp.loc[residual_max_idx]

    return (
        f"Thành phần trend thay đổi khoảng **{pct(trend_growth)}** trong toàn kỳ. "
        f"Biên độ seasonality khoảng **{md_money(seasonal_amp)}**, cho thấy yếu tố mùa vụ có ảnh hưởng nhất định. "
        f"Residual lớn nhất ở tháng **{residual_row['month_start'].date()}**, vì vậy tháng này nên được xem là điểm biến động cần kiểm tra thêm."
    )


def build_scenario_insight(scenario):
    if scenario.empty:
        return "Chưa có dữ liệu scenario."

    first_month = scenario["month_start"].min()
    first = scenario[scenario["month_start"] == first_month]

    worst = first[first["scenario_name"] == "Worst Case"]["forecast_revenue"].iloc[0]
    normal = first[first["scenario_name"] == "Normal Case"]["forecast_revenue"].iloc[0]
    best = first[first["scenario_name"] == "Best Case"]["forecast_revenue"].iloc[0]

    return (
        f"Ở tháng {first_month.date()}, Normal Case là **{md_money(normal)}**. "
        f"Worst Case khoảng **{md_money(worst)}** và Best Case khoảng **{md_money(best)}**. "
        "Ba kịch bản này dùng để tham khảo khi lập kế hoạch, không phải ba dự báo độc lập."
    )


def build_whatif_insight(what_if, impact):
    if what_if.empty:
        return "Chưa có dữ liệu What-if."

    base_total = what_if["forecast_revenue"].sum()
    adjusted_total = what_if["adjusted_forecast"].sum()
    diff = adjusted_total - base_total

    return (
        f"Nếu giả định điều kiện kinh doanh làm doanh thu thay đổi **{impact:+d}%**, "
        f"tổng forecast trong kỳ sẽ thay đổi từ **{md_money(base_total)}** thành **{md_money(adjusted_total)}** "
        f"(chênh lệch **{md_money(diff)}**). Đây là mô phỏng kịch bản, không phải kết quả model mới."
    )


def build_executive_comment(s):
    best_wape = safe_float(s.get("best_wape"))
    risk = s.get("risk_level", "N/A")
    model = s.get("best_model", "N/A")

    return (
        f"Mô hình **{model}** được chọn vì có WAPE thấp nhất trong các mô hình thử nghiệm "
        f"(**{pct(best_wape)}**). Forecast tháng tới khoảng **{md_money(s.get('next_month_forecast'))}**. "
        f"Với Risk Level **{risk}**, kết quả phù hợp để hỗ trợ lập kế hoạch ngắn hạn "
        "và nên được cập nhật khi có dữ liệu thực tế mới."
    )


def dashboard_recommendation(s):
    risk = str(s.get("risk_level", "Medium"))

    if risk == "Low":
        return (
            "Có thể dùng forecast làm cơ sở lập kế hoạch bán hàng và tồn kho ở mức hợp lý. "
            "Vẫn nên theo dõi doanh thu thực tế để điều chỉnh khi cần."
        )

    if risk == "Medium":
        return (
            "Nên dùng forecast như kịch bản tham khảo cho lập kế hoạch. "
            "Theo dõi doanh thu thực tế, gross margin và cập nhật lại mô hình khi có dữ liệu tháng mới."
        )

    return (
        "Forecast chỉ nên dùng để tham khảo vì mức rủi ro cao. "
        "Cần theo dõi sát doanh thu thực tế trước khi đưa ra quyết định tồn kho hoặc ngân sách lớn."
    )


# 5. Page title


st.title("TV3 - Sales Intelligence Dashboard")
st.caption(
    "Dashboard đọc dữ liệu từ DataMart và các bảng analytics để trình bày "
    "EDA, Forecast, Model Ranking, Scenario và What-if."
)

try:
    actual, forecast, metrics, decomp, scenario, summary = load_all()
except Exception as exc:
    st.error("Chưa đọc được dữ liệu. Hãy chạy script `tv3_sales_intelligence.py` trước.")
    st.exception(exc)
    st.stop()

if summary.empty:
    st.warning("Chưa có bảng `analytics.sales_forecast_summary`.")
    st.stop()

s = summary.iloc[0]

# Dữ liệu thực tế trong DataMart có thể chứa tháng cuối chưa hoàn chỉnh.
# Dashboard sẽ dùng đến current_month trong summary để EDA/biểu đồ không bị kéo lệch bởi tháng incomplete.
current_month = pd.to_datetime(s.get("current_month")) if pd.notna(s.get("current_month")) else actual["month_start"].max()
actual_eda = actual[actual["month_start"] <= current_month].copy()
excluded_actual = actual[actual["month_start"] > current_month].copy()


# 6. KPI cards

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Current Revenue", money(s.get("current_revenue")))
c2.metric("Next Forecast", money(s.get("next_month_forecast")))
c3.metric("Best Model", s.get("best_model", "N/A"))
c4.metric("Reliability Score", f"{float(s.get('forecast_accuracy_score', 0)):.1f}/100")
c5.metric("Risk Level", s.get("risk_level", "N/A"))

st.info(build_executive_comment(s))

st.divider()


# 7. EDA section

st.header("A. Exploratory Data Analysis")

eda1, eda2, eda3, eda4 = st.columns(4)

eda1.metric("Complete Months", len(actual_eda))
eda2.metric("Total Revenue", money(actual_eda["revenue"].sum()))
eda3.metric("Total Orders", number(actual_eda["order_count"].sum()))
eda4.metric("Avg Gross Margin", pct(actual_eda["gross_margin"].mean()))

left, right = st.columns(2)

with left:
    st.subheader("1. Revenue Trend")
    fig = px.line(actual_eda, x="month_start", y="revenue", markers=True, title="Monthly Revenue Trend (complete months)")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("2. Order Count Trend")
    fig = px.line(actual_eda, x="month_start", y="order_count", markers=True, title="Monthly Order Count Trend (complete months)")
    st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("3. Quantity Sold Trend")
    fig = px.line(actual_eda, x="month_start", y="quantity_sold", markers=True, title="Monthly Quantity Sold Trend (complete months)")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("4. Gross Margin Trend")
    fig = px.line(actual_eda, x="month_start", y="gross_margin", markers=True, title="Estimated Gross Margin Trend (complete months)")
    fig.update_layout(yaxis_tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)


# Additional EDA: Month / Quarter / Year, Growth, Profit, Revenue Driver
eda_features = prepare_eda_features(actual_eda)

st.subheader("5. Revenue by Month / Quarter / Year")
tab_month, tab_quarter, tab_year = st.tabs(["Monthly", "Quarterly", "Yearly"])

with tab_month:
    fig_month = px.line(
        eda_features,
        x="month_start",
        y="revenue",
        markers=True,
        title="Monthly Revenue"
    )
    st.plotly_chart(fig_month, use_container_width=True)

with tab_quarter:
    quarter_df = eda_features.groupby("quarter", as_index=False)["revenue"].sum()
    fig_quarter = px.bar(
        quarter_df,
        x="quarter",
        y="revenue",
        text_auto=".2s",
        title="Quarterly Revenue"
    )
    fig_quarter.update_layout(xaxis_title="Quarter", yaxis_title="Revenue")
    st.plotly_chart(fig_quarter, use_container_width=True)

with tab_year:
    year_df = eda_features.groupby("year", as_index=False)["revenue"].sum()
    fig_year = px.bar(
        year_df,
        x="year",
        y="revenue",
        text_auto=".2s",
        title="Yearly Revenue"
    )
    fig_year.update_layout(xaxis_title="Year", yaxis_title="Revenue")
    st.plotly_chart(fig_year, use_container_width=True)

st.markdown("**Insight theo thời gian:**")
st.markdown(build_time_level_insight(eda_features))

st.subheader("6. Revenue Growth")
growth_plot = eda_features.dropna(subset=["mom_growth"]).copy()
growth_plot["mom_growth_pct"] = growth_plot["mom_growth"] * 100
growth_plot["yoy_growth_pct"] = growth_plot["yoy_growth"] * 100

left, right = st.columns(2)
with left:
    fig_mom = px.bar(
        growth_plot,
        x="month_start",
        y="mom_growth_pct",
        title="MoM Revenue Growth (%)"
    )
    fig_mom.update_layout(xaxis_title="Month", yaxis_title="MoM Growth (%)")
    st.plotly_chart(fig_mom, use_container_width=True)

with right:
    yoy_plot = growth_plot.dropna(subset=["yoy_growth_pct"])
    if yoy_plot.empty:
        st.info("Chưa đủ 12 tháng để vẽ YoY Growth.")
    else:
        fig_yoy = px.line(
            yoy_plot,
            x="month_start",
            y="yoy_growth_pct",
            markers=True,
            title="YoY Revenue Growth (%)"
        )
        fig_yoy.update_layout(xaxis_title="Month", yaxis_title="YoY Growth (%)")
        st.plotly_chart(fig_yoy, use_container_width=True)

st.markdown("**Insight tăng trưởng:**")
st.markdown(build_growth_insight(eda_features))

st.subheader("7. Gross Profit and Gross Margin")
left, right = st.columns(2)
with left:
    fig_gp = px.line(
        eda_features,
        x="month_start",
        y="gross_profit",
        markers=True,
        title="Monthly Gross Profit"
    )
    st.plotly_chart(fig_gp, use_container_width=True)

with right:
    fig_gm = px.line(
        eda_features,
        x="month_start",
        y="gross_margin",
        markers=True,
        title="Monthly Gross Margin (%)"
    )
    fig_gm.update_layout(yaxis_tickformat=".0%")
    st.plotly_chart(fig_gm, use_container_width=True)

st.markdown("**Insight lợi nhuận:**")
st.markdown(build_profit_insight(eda_features))

st.subheader("8. Revenue Driver Analysis")
driver_df = eda_features[["month_start", "revenue", "order_count", "quantity_sold", "aov"]].copy()
# Chuẩn hóa về index 100 để so sánh xu hướng các chỉ số khác đơn vị.
for col in ["revenue", "order_count", "quantity_sold", "aov"]:
    first_valid = driver_df[col].replace(0, pd.NA).dropna()
    if not first_valid.empty:
        driver_df[col + "_index"] = driver_df[col] / first_valid.iloc[0] * 100
    else:
        driver_df[col + "_index"] = pd.NA

driver_long = driver_df.melt(
    id_vars="month_start",
    value_vars=["revenue_index", "order_count_index", "quantity_sold_index", "aov_index"],
    var_name="metric",
    value_name="index_value"
)
driver_long["metric"] = driver_long["metric"].map({
    "revenue_index": "Revenue",
    "order_count_index": "Order Count",
    "quantity_sold_index": "Quantity Sold",
    "aov_index": "Average Order Value"
})

fig_driver = px.line(
    driver_long,
    x="month_start",
    y="index_value",
    color="metric",
    markers=True,
    title="Revenue Driver Index (Start = 100)"
)
fig_driver.update_layout(xaxis_title="Month", yaxis_title="Index")
st.plotly_chart(fig_driver, use_container_width=True)

st.markdown("**Insight động lực doanh thu:**")
st.markdown(build_driver_insight(eda_features))

st.markdown("**Insight EDA:**")
if not excluded_actual.empty:
    excluded_months = ", ".join(excluded_actual["month_start"].dt.strftime("%Y-%m").tolist())
    st.warning(
        f"Tháng {excluded_months} không được dùng trong EDA/forecast chính vì nằm sau current_month trong summary. "
        "Tháng này có thể chưa hoàn chỉnh hoặc chưa phù hợp để đánh giá xu hướng."
    )

for item in build_eda_insights(actual_eda):
    st.markdown(f"- {item}")


st.divider()


# 8. Model ranking

st.header("B. Forecast Model Comparison")

st.subheader("5. Model Ranking")

show_metrics = metrics.copy()
show_metrics = show_metrics.drop(columns=["mape"], errors="ignore")
show_metrics = show_metrics.rename(columns={
    "model_name": "Model",
    "mae": "MAE",
    "rmse": "RMSE",
    "wape": "WAPE",
    "accuracy": "Confidence",
    "model_rank": "Rank"
})

for col in ["MAE", "RMSE"]:
    if col in show_metrics.columns:
        show_metrics[col] = show_metrics[col].map(lambda x: f"{float(x):,.0f}")

for col in ["WAPE", "Confidence"]:
    if col in show_metrics.columns:
        show_metrics[col] = show_metrics[col].map(lambda x: f"{float(x):.1%}")

st.dataframe(show_metrics, use_container_width=True, hide_index=True)

metric_plot = metrics.copy()
metric_plot["wape_pct"] = metric_plot["wape"] * 100

fig_metric = px.bar(
    metric_plot,
    x="model_name",
    y="wape_pct",
    text="model_rank",
    title="Model Ranking by WAPE (%)"
)

fig_metric.update_traces(textposition="inside")
fig_metric.update_layout(xaxis_title="Model", yaxis_title="WAPE (%)")
st.plotly_chart(fig_metric, use_container_width=True)

st.markdown("**Insight model ranking:**")
st.markdown(build_model_ranking_insight(metrics))

st.divider()


# 9. Actual vs Forecast

st.header("C. Forecast Result")

if forecast.empty:
    st.warning("Chưa có bảng `analytics.sales_forecast`.")
    st.stop()

model_options = forecast["model_name"].dropna().unique().tolist()

if not model_options:
    st.warning("Không có model forecast để hiển thị.")
    st.stop()

default_model = s.get("best_model") if s.get("best_model") in model_options else model_options[0]

model = st.selectbox("Chọn model", model_options, index=model_options.index(default_model))
model_df = forecast[forecast["model_name"] == model].copy()

test_df = model_df[model_df["dataset_type"] == "test"]
future_df = model_df[model_df["dataset_type"] == "future"]

fig2 = go.Figure()

if not test_df.empty:
    fig2.add_trace(go.Scatter(
        x=test_df["month_start"],
        y=test_df["actual_revenue"],
        mode="lines+markers",
        name="Actual"
    ))
    fig2.add_trace(go.Scatter(
        x=test_df["month_start"],
        y=test_df["forecast_revenue"],
        mode="lines+markers",
        name="Forecast Test"
    ))

if not future_df.empty:
    fig2.add_trace(go.Scatter(
        x=future_df["month_start"],
        y=future_df["forecast_revenue"],
        mode="lines+markers",
        name="Future Forecast"
    ))

    if {"forecast_upper", "forecast_lower"}.issubset(future_df.columns):
        fig2.add_trace(go.Scatter(
            x=future_df["month_start"],
            y=future_df["forecast_upper"],
            mode="lines",
            name="Upper Bound",
            line=dict(width=0),
            showlegend=False
        ))
        fig2.add_trace(go.Scatter(
            x=future_df["month_start"],
            y=future_df["forecast_lower"],
            mode="lines",
            name="Lower Bound",
            fill="tonexty",
            line=dict(width=0),
            showlegend=False
        ))

fig2.update_layout(title=f"Actual vs Forecast - {model}", xaxis_title="Month", yaxis_title="Revenue")
st.plotly_chart(fig2, use_container_width=True)

st.markdown("**Insight Actual vs Forecast:**")
st.markdown(build_forecast_insight(test_df, future_df, model, metrics))

st.divider()


# 10. Decomposition

st.header("D. Trend - Seasonality - Residual")

if decomp.empty:
    st.warning("Dữ liệu chưa đủ dài để decomposition theo mùa vụ 12 tháng.")
else:
    component = st.radio(
        "Chọn thành phần",
        ["observed", "trend", "seasonal", "residual"],
        horizontal=True
    )

    fig3 = px.line(
        decomp,
        x="month_start",
        y=component,
        title=f"Time Series Decomposition - {component}"
    )

    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("**Insight decomposition:**")
    st.markdown(build_decomposition_insight(decomp))

st.divider()


# 11. Scenario

st.header("E. Forecast Scenario")

if scenario.empty:
    st.warning("Chưa có bảng scenario.")
else:
    fig4 = px.line(
        scenario,
        x="month_start",
        y="forecast_revenue",
        color="scenario_name",
        markers=True,
        title="Best / Normal / Worst Case Forecast"
    )

    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("**Insight scenario:**")
    st.markdown(build_scenario_insight(scenario))

st.divider()


# 12. What-if

st.header("F. What-if Analysis")

if future_df.empty:
    st.warning("Model đang chọn không có future forecast.")
else:
    st.caption("Phần này chỉ mô phỏng tác động giả định của điều kiện kinh doanh lên forecast, không phải model dự báo mới.")
    impact = st.slider(
        "Giả định tác động nhu cầu/kinh doanh lên doanh thu (%)",
        min_value=-20,
        max_value=20,
        value=0,
        step=5
    )

    what_if = future_df[["month_start", "forecast_revenue"]].copy()
    what_if["adjusted_forecast"] = what_if["forecast_revenue"] * (1 + impact / 100)

    fig5 = go.Figure()

    fig5.add_trace(go.Scatter(
        x=what_if["month_start"],
        y=what_if["forecast_revenue"],
        mode="lines+markers",
        name="Original Forecast"
    ))

    fig5.add_trace(go.Scatter(
        x=what_if["month_start"],
        y=what_if["adjusted_forecast"],
        mode="lines+markers",
        name=f"What-if {impact:+d}%"
    ))

    fig5.update_layout(title="What-if Forecast Simulation", xaxis_title="Month", yaxis_title="Revenue")
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown("**Insight What-if:**")
    st.markdown(build_whatif_insight(what_if, impact))

st.divider()


# 13. Executive summary
st.header("G. Forecast Summary")


st.markdown(f"""
**Tóm tắt:**

- Model được chọn: **{s.get('best_model')}**
- WAPE: **{pct(s.get('best_wape'))}**
- Forecast tháng tới: **{md_money(s.get('next_month_forecast'))}**
- Risk Level: **{s.get('risk_level')}**

**Nhận xét:**  
{build_executive_comment(s)}

**Khuyến nghị:**  
{dashboard_recommendation(s)}
""")