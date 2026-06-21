from __future__ import annotations

import math
import os

import mlflow
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX

from aw_analytics.db import engine, ensure_analytics_schema
from aw_analytics.tracking import configure_mlflow


def fit_model(series: pd.Series):
    return SARIMAX(
        series,
        order=(1, 1, 1),
        seasonal_order=(1, 1, 1, 12),
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit(disp=False)


def run_sales_forecast(horizon: int | None = None) -> pd.DataFrame:
    ensure_analytics_schema()
    horizon = horizon or int(os.getenv("FORECAST_HORIZON_MONTHS", "6"))
    db_engine = engine()
    monthly = pd.read_sql(
        "select month, revenue from analytics.feature_monthly_sales order by month",
        db_engine,
        parse_dates=["month"],
    ).set_index("month")
    series = monthly["revenue"].asfreq("MS").fillna(0)

    holdout = min(6, max(1, len(series) // 5))
    train, test = series.iloc[:-holdout], series.iloc[-holdout:]
    evaluation_model = fit_model(train)
    prediction = evaluation_model.get_forecast(holdout).predicted_mean
    mae = mean_absolute_error(test, prediction)
    rmse = math.sqrt(mean_squared_error(test, prediction))

    model = fit_model(series)
    forecast = model.get_forecast(horizon)
    interval = forecast.conf_int()
    output = pd.DataFrame(
        {
            "month": forecast.predicted_mean.index,
            "predicted_revenue": forecast.predicted_mean.values,
            "lower_bound": interval.iloc[:, 0].values,
            "upper_bound": interval.iloc[:, 1].values,
            "model_name": "sarimax_111_111_12",
            "model_version": "1",
            "scored_at": pd.Timestamp.now(tz="UTC"),
        }
    )

    configure_mlflow("sales_forecast")
    with mlflow.start_run():
        mlflow.log_param("horizon_months", horizon)
        mlflow.log_param("holdout_months", holdout)
        mlflow.log_metric("mae", mae)
        mlflow.log_metric("rmse", rmse)

    output.to_sql(
        "sales_forecast",
        db_engine,
        schema="analytics",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )
    return output


if __name__ == "__main__":
    result = run_sales_forecast()
    print(f"Forecasted {len(result)} months.")
