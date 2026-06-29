import os
import warnings
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose

warnings.filterwarnings("ignore")


@dataclass
class Config:
    db_user: str = os.getenv("POSTGRES_USER", "postgres")
    db_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_host: str = os.getenv("DB_HOST", os.getenv("SOURCE_HOST", "localhost"))
    db_port: str = os.getenv("DB_PORT", os.getenv("SOURCE_INTERNAL_PORT", "5432"))
    db_name: str = os.getenv("SOURCE_DATABASE", "Adventureworks")
    test_size: int = int(os.getenv("TV3_TEST_SIZE", "6"))
    forecast_horizon: int = int(os.getenv("TV3_FORECAST_HORIZON", "6"))
    season_length: int = int(os.getenv("TV3_SEASON_LENGTH", "12"))

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


def safe_divide(a, b):
    if b is None or pd.isna(b) or b == 0:
        return np.nan
    return float(a / b)


def wape(y_true, y_pred):
    denominator = np.sum(np.abs(y_true))
    return safe_divide(np.sum(np.abs(y_true - y_pred)), denominator)


def mape(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mask = y_true != 0
    if not mask.any():
        return np.nan

    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])))


def load_monthly_sales(engine):
    query = """
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
    """

    df = pd.read_sql(query, engine)
    df.columns = [c.lower() for c in df.columns]

    out = pd.DataFrame()
    out["month_start"] = pd.to_datetime(df["month"]).dt.to_period("M").dt.to_timestamp()
    out["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0.0)
    out["order_count"] = pd.to_numeric(df["order_count"], errors="coerce").fillna(0.0)
    out["quantity_sold"] = pd.to_numeric(df["quantity_sold"], errors="coerce").fillna(0.0)
    out["estimated_cogs"] = pd.to_numeric(df["estimated_cogs"], errors="coerce").fillna(0.0)
    out["gross_profit"] = pd.to_numeric(df["estimated_gross_profit"], errors="coerce").fillna(0.0)
    out["gross_margin"] = pd.to_numeric(df["estimated_gross_margin_pct"], errors="coerce")

    out = out.sort_values("month_start")
    out = out.set_index("month_start").asfreq("MS")

    for col in ["revenue", "order_count", "quantity_sold", "estimated_cogs", "gross_profit", "gross_margin"]:
        out[col] = out[col].interpolate().fillna(0.0)

    out = out.reset_index()

    recent_median = out["revenue"].tail(12).median()
    last_revenue = out["revenue"].iloc[-1]

    if last_revenue < recent_median * 0.3:
        print(
            f"Last month {out['month_start'].iloc[-1].date()} looks incomplete "
            f"(revenue={last_revenue:,.0f}, recent median={recent_median:,.0f}). "
            "It will be excluded from modeling."
        )
        out = out.iloc[:-1].copy()

    return out




def build_territory_sales(engine):
    query = """
        select
            date_trunc('month', h.orderdate)::date as month_start,
            coalesce(t.name, 'Unknown') as territory,
            coalesce(t.countryregioncode, 'Unknown') as country,
            coalesce(t."group", 'Unknown') as territory_group,
            count(distinct h.salesorderid) as order_count,
            sum(d.orderqty) as quantity_sold,
            sum(d.orderqty * d.unitprice * (1 - coalesce(d.unitpricediscount, 0))) as revenue,
            sum(d.orderqty * coalesce(p.standardcost, 0)) as estimated_cogs,
            sum(
                d.orderqty * d.unitprice * (1 - coalesce(d.unitpricediscount, 0))
                - d.orderqty * coalesce(p.standardcost, 0)
            ) as gross_profit,
            case
                when sum(d.orderqty * d.unitprice * (1 - coalesce(d.unitpricediscount, 0))) = 0 then null
                else
                    sum(
                        d.orderqty * d.unitprice * (1 - coalesce(d.unitpricediscount, 0))
                        - d.orderqty * coalesce(p.standardcost, 0)
                    )
                    / sum(d.orderqty * d.unitprice * (1 - coalesce(d.unitpricediscount, 0)))
            end as gross_margin
        from sales.salesorderheader h
        join sales.salesorderdetail d
            on h.salesorderid = d.salesorderid
        join production.product p
            on d.productid = p.productid
        left join sales.salesterritory t
            on h.territoryid = t.territoryid
        group by
            date_trunc('month', h.orderdate)::date,
            coalesce(t.name, 'Unknown'),
            coalesce(t.countryregioncode, 'Unknown'),
            coalesce(t."group", 'Unknown')
        order by
            month_start,
            territory
    """

    try:
        territory_df = pd.read_sql(query, engine)
        territory_df.columns = [c.lower() for c in territory_df.columns]

        for col in [
            "order_count", "quantity_sold", "revenue",
            "estimated_cogs", "gross_profit", "gross_margin"
        ]:
            territory_df[col] = pd.to_numeric(territory_df[col], errors="coerce")

        territory_df["month_start"] = pd.to_datetime(territory_df["month_start"]).dt.date
        return territory_df

    except Exception as exc:
        print(f"Territory analysis skipped: {exc}")
        return pd.DataFrame(columns=[
            "month_start", "territory", "country", "territory_group",
            "order_count", "quantity_sold", "revenue",
            "estimated_cogs", "gross_profit", "gross_margin"
        ])


def split_train_test(df, test_size=6):
    """Chia train/test theo thứ tự thời gian, không shuffle."""
    train = df.iloc[:-test_size].copy()
    test = df.iloc[-test_size:].copy()

    return train, test


def forecast_seasonal_naive(train, dates, season_length):
    train_indexed = train.set_index("month_start")
    values = []

    for date in dates:
        prev = pd.Timestamp(date) - pd.DateOffset(months=season_length)

        if prev in train_indexed.index:
            values.append(float(train_indexed.loc[prev, "revenue"]))
        else:
            values.append(float(train["revenue"].iloc[-1]))

    return np.asarray(values)


def forecast_moving_average(train, horizon, window=3):
    avg = float(train["revenue"].tail(window).mean())
    return np.repeat(avg, horizon)


def forecast_linear_trend(train, horizon):
    x = np.arange(len(train)).reshape(-1, 1)
    y = train["revenue"].values

    model = LinearRegression()
    model.fit(x, y)

    future_x = np.arange(len(train), len(train) + horizon).reshape(-1, 1)
    pred = model.predict(future_x)

    return np.maximum(pred, 0)


def forecast_holt_winters(train, horizon, season_length):
    y = train.set_index("month_start")["revenue"].asfreq("MS")

    if len(y) >= season_length * 2:
        model = ExponentialSmoothing(
            y,
            trend="add",
            seasonal="add",
            seasonal_periods=season_length
        )
    else:
        model = ExponentialSmoothing(
            y,
            trend="add",
            seasonal=None
        )

    fitted = model.fit(optimized=True)
    pred = fitted.forecast(horizon)

    return np.maximum(pred.values, 0)


def try_forecast_sarima(train, horizon, season_length):
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        y = train.set_index("month_start")["revenue"].asfreq("MS")

        if len(y) >= season_length * 2:
            model = SARIMAX(
                y,
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, season_length),
                enforce_stationarity=False,
                enforce_invertibility=False
            )
        else:
            model = SARIMAX(
                y,
                order=(1, 1, 1),
                enforce_stationarity=False,
                enforce_invertibility=False
            )

        fitted = model.fit(disp=False)
        pred = fitted.forecast(horizon)

        return np.maximum(pred.values, 0)

    except Exception as exc:
        print(f"SARIMA skipped: {exc}")
        return np.array([])


def evaluate_model(y_true, y_pred, model_name):
    return {
        "model_name": model_name,
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mape": mape(y_true, y_pred),
        "wape": wape(y_true, y_pred),
        "accuracy": 1 - wape(y_true, y_pred)
    }


def build_model_predictions(train, test, cfg):
    y_true = test["revenue"].values
    horizon = len(test)

    preds = {
        "Seasonal Naive": forecast_seasonal_naive(train, test["month_start"], cfg.season_length),
        "Moving Average": forecast_moving_average(train, horizon),
        "Linear Trend": forecast_linear_trend(train, horizon),
        "Holt-Winters": forecast_holt_winters(train, horizon, cfg.season_length)
    }

    sarima_pred = try_forecast_sarima(train, horizon, cfg.season_length)
    if len(sarima_pred) == horizon:
        preds["SARIMA"] = sarima_pred

    forecast_rows = []
    metric_rows = []

    for model_name, pred in preds.items():
        metric_rows.append(evaluate_model(y_true, pred, model_name))

        for date, actual, forecast in zip(test["month_start"], y_true, pred):
            forecast_rows.append({
                "month_start": date.date(),
                "actual_revenue": float(actual),
                "forecast_revenue": float(forecast),
                "forecast_lower": float(max(forecast * 0.90, 0)),
                "forecast_upper": float(forecast * 1.10),
                "model_name": model_name,
                "dataset_type": "test"
            })

    metric_df = pd.DataFrame(metric_rows)
    metric_df = metric_df.sort_values(["wape", "rmse"]).reset_index(drop=True)
    metric_df["model_rank"] = np.arange(1, len(metric_df) + 1)

    return pd.DataFrame(forecast_rows), metric_df


def build_future_forecast(df, best_model, cfg):
    last_month = pd.Timestamp(df["month_start"].max())

    future_dates = pd.date_range(
        last_month + pd.DateOffset(months=1),
        periods=cfg.forecast_horizon,
        freq="MS"
    )

    horizon = len(future_dates)

    if best_model == "Seasonal Naive":
        pred = forecast_seasonal_naive(df, pd.Series(future_dates), cfg.season_length)
    elif best_model == "Moving Average":
        pred = forecast_moving_average(df, horizon)
    elif best_model == "Linear Trend":
        pred = forecast_linear_trend(df, horizon)
    elif best_model == "SARIMA":
        pred = try_forecast_sarima(df, horizon, cfg.season_length)

        if len(pred) != horizon:
            pred = forecast_holt_winters(df, horizon, cfg.season_length)
            best_model = "Holt-Winters"
    else:
        pred = forecast_holt_winters(df, horizon, cfg.season_length)

    rows = []

    for date, forecast in zip(future_dates, pred):
        rows.append({
            "month_start": date.date(),
            "actual_revenue": None,
            "forecast_revenue": float(forecast),
            "forecast_lower": float(max(forecast * 0.90, 0)),
            "forecast_upper": float(forecast * 1.10),
            "model_name": best_model,
            "dataset_type": "future"
        })

    return pd.DataFrame(rows)


def build_decomposition(df, cfg):
    y = df.set_index("month_start")["revenue"].asfreq("MS")

    if len(y) < cfg.season_length * 2:
        return pd.DataFrame(
            columns=["month_start", "observed", "trend", "seasonal", "residual"]
        )

    decomp = seasonal_decompose(
        y,
        model="additive",
        period=cfg.season_length,
        extrapolate_trend="freq"
    )

    out = pd.DataFrame({
        "month_start": decomp.observed.index.date,
        "observed": decomp.observed.values,
        "trend": decomp.trend.values,
        "seasonal": decomp.seasonal.values,
        "residual": decomp.resid.values
    })

    return out.replace([np.inf, -np.inf], np.nan)


def build_scenarios(future_df):
    rows = []

    scenario_map = {
        "Worst Case": 0.90,
        "Normal Case": 1.00,
        "Best Case": 1.10
    }

    for _, row in future_df.iterrows():
        for scenario, factor in scenario_map.items():
            rows.append({
                "month_start": row["month_start"],
                "scenario_name": scenario,
                "forecast_revenue": float(row["forecast_revenue"] * factor),
                "model_name": row["model_name"]
            })

    return pd.DataFrame(rows)


def classify_risk(growth_pct, best_wape):
    if pd.isna(growth_pct) or pd.isna(best_wape):
        return "Medium"

    if growth_pct < -0.05 or best_wape > 0.25:
        return "High"

    if growth_pct < 0.02 or best_wape > 0.15:
        return "Medium"

    return "Low"


def recommendation_text(growth_pct, risk_level):
    growth_display = f"{growth_pct:.1%}" if not pd.isna(growth_pct) else "N/A"

    if risk_level == "Low":
        return (
            f"Forecast tăng {growth_display}. "
            "Nên chủ động lập kế hoạch bán hàng, chuẩn bị tồn kho phù hợp "
            "và triển khai các chương trình marketing để tận dụng xu hướng tăng trưởng."
        )

    if risk_level == "Medium":
       return (
            f"Forecast ở mức cần theo dõi ({growth_display}). "
            "Nên kiểm soát tồn kho, theo dõi doanh thu thực tế và gross margin, "
            "đồng thời ưu tiên các sản phẩm có biên lợi nhuận cao."
        )

    return (
        f"Forecast có rủi ro ({growth_display}) hoặc sai số mô hình còn cao. "
        "Nên theo dõi doanh thu thực tế theo tuần, hạn chế mở rộng tồn kho "
        "và cập nhật mô hình khi có thêm dữ liệu."
    )


def build_executive_summary(df, metric_df, future_df):
    recent_median = df["revenue"].tail(12).median()
    valid_df = df[df["revenue"] >= recent_median * 0.3].copy()

    if len(valid_df) >= 2:
        summary_df = valid_df
    else:
        summary_df = df

    current_revenue = float(summary_df["revenue"].iloc[-1])
    previous_revenue = float(summary_df["revenue"].iloc[-2]) if len(summary_df) >= 2 else np.nan
    next_forecast = float(future_df["forecast_revenue"].iloc[0])

    growth_vs_current = safe_divide(next_forecast - current_revenue, current_revenue)
    recent_growth = safe_divide(current_revenue - previous_revenue, previous_revenue)

    best = metric_df.sort_values(["wape", "rmse"]).iloc[0]
    best_wape = float(best["wape"])

    accuracy_score = max(0.0, min(100.0, (1 - best_wape) * 100))
    growth_component = 50 + max(-50, min(50, (recent_growth if not pd.isna(recent_growth) else 0) * 100))
    future_component = 80 if growth_vs_current >= 0 else 50

    health_score = np.nanmean([
        accuracy_score,
        growth_component,
        future_component
    ])

    risk_level = classify_risk(growth_vs_current, best_wape)

    return pd.DataFrame([{
        "current_month": summary_df["month_start"].iloc[-1].date(),
        "current_revenue": current_revenue,
        "next_month": future_df["month_start"].iloc[0],
        "next_month_forecast": next_forecast,
        "growth_vs_current": growth_vs_current,
        "best_model": best["model_name"],
        "best_wape": best_wape,
        "forecast_accuracy_score": accuracy_score,
        "revenue_health_score": float(health_score),
        "risk_level": risk_level,
        "recommendation": recommendation_text(growth_vs_current, risk_level)
    }])


def save_outputs(engine, forecast_df, metric_df, future_df, decomp_df, scenario_df, summary_df, territory_df):
    full_forecast_df = pd.concat([forecast_df, future_df], ignore_index=True)

    with engine.begin() as conn:
        conn.execute(text("create schema if not exists analytics"))

        for table in [
            "sales_forecast",
            "sales_forecast_metric",
            "sales_forecast_decomposition",
            "sales_forecast_scenario",
            "sales_forecast_summary",
            "sales_territory_monthly"
        ]:
            conn.execute(text(f"drop table if exists analytics.{table}"))

    full_forecast_df.to_sql(
        "sales_forecast",
        engine,
        schema="analytics",
        if_exists="replace",
        index=False
    )

    metric_df.to_sql(
        "sales_forecast_metric",
        engine,
        schema="analytics",
        if_exists="replace",
        index=False
    )

    decomp_df.to_sql(
        "sales_forecast_decomposition",
        engine,
        schema="analytics",
        if_exists="replace",
        index=False
    )

    scenario_df.to_sql(
        "sales_forecast_scenario",
        engine,
        schema="analytics",
        if_exists="replace",
        index=False
    )

    summary_df.to_sql(
        "sales_forecast_summary",
        engine,
        schema="analytics",
        if_exists="replace",
        index=False
    )

    territory_df.to_sql(
        "sales_territory_monthly",
        engine,
        schema="analytics",
        if_exists="replace",
        index=False
    )


def main():
    cfg = Config()
    engine = create_engine(cfg.db_url)

    print("Loading monthly sales...")
    df = load_monthly_sales(engine)

    print(
        f"Loaded {len(df)} monthly rows from "
        f"{pd.Timestamp(df['month_start'].min()).date()} to "
        f"{pd.Timestamp(df['month_start'].max()).date()}."
    )

    train, test = split_train_test(df, cfg.test_size)

    print(f"Train rows: {len(train)}, test rows: {len(test)}")

    forecast_df, metric_df = build_model_predictions(train, test, cfg)

    best_model = metric_df.iloc[0]["model_name"]

    print("Model ranking:")
    print(metric_df.to_string(
        index=False,
        formatters={
            "mae": "{:,.2f}".format,
            "rmse": "{:,.2f}".format,
            "mape": "{:.4f}".format,
            "wape": "{:.4f}".format,
            "accuracy": "{:.4f}".format,
        }
    ))

    future_df = build_future_forecast(df, best_model, cfg)
    decomp_df = build_decomposition(df, cfg)
    scenario_df = build_scenarios(future_df)
    summary_df = build_executive_summary(df, metric_df, future_df)
    territory_df = build_territory_sales(engine)

    save_outputs(
        engine,
        forecast_df,
        metric_df,
        future_df,
        decomp_df,
        scenario_df,
        summary_df,
        territory_df
    )

    print("Saved outputs to analytics schema:")
    print("- analytics.sales_forecast")
    print("- analytics.sales_forecast_metric")
    print("- analytics.sales_forecast_decomposition")
    print("- analytics.sales_forecast_scenario")
    print("- analytics.sales_forecast_summary")
    print("- analytics.sales_territory_monthly")

    print("Executive summary:")
    print(summary_df.T)


if __name__ == "__main__":
    main()