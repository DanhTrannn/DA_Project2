from __future__ import annotations

import mlflow
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from aw_analytics.db import engine, ensure_analytics_schema
from aw_analytics.tracking import configure_mlflow


FEATURES = ["recency_days", "frequency", "monetary", "average_order_value"]
K_RANGE = range(3, 7)
SELECTED_K = 5


def build_pipeline(n_clusters: int) -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            ("model", KMeans(n_clusters=n_clusters, random_state=42, n_init=20)),
        ]
    )

def build_customer_analytics_tables(db_engine) -> None:
    with db_engine.begin() as conn:
        conn.exec_driver_sql(
            """
            DROP TABLE IF EXISTS analytics.customer_segment_summary;

            CREATE TABLE analytics.customer_segment_summary AS
            SELECT
                s.segment_name,
                COUNT(*) AS customer_count,
                SUM(COALESCE(b.revenue, 0)) AS total_revenue,
                AVG(COALESCE(b.revenue, 0)) AS avg_revenue,
                SUM(COALESCE(b.estimated_gross_profit, 0)) AS total_gross_profit,
                AVG(COALESCE(b.estimated_gross_profit, 0)) AS avg_gross_profit,
                AVG(COALESCE(b.estimated_gross_margin_pct, 0)) AS avg_gross_margin_pct,
                AVG(s.recency_days) AS avg_recency,
                AVG(s.frequency) AS avg_frequency,
                AVG(s.monetary) AS avg_monetary,
                AVG(s.average_order_value) AS avg_order_value
            FROM analytics.customer_segment s
            LEFT JOIN mart_customer.customer_base b
                ON s.customer_key = b.customer_key
            GROUP BY s.segment_name;
            """
        )

        conn.exec_driver_sql(
            """
            DROP TABLE IF EXISTS analytics.customer_top_value;

            CREATE TABLE analytics.customer_top_value AS
            SELECT
                s.customer_key,
                s.customer_name,
                s.customer_type,
                s.country_code,
                s.segment_name,
                b.territory_name,
                b.revenue,
                b.estimated_gross_profit,
                b.estimated_gross_margin_pct,
                s.recency_days,
                s.frequency,
                s.monetary,
                s.average_order_value
            FROM analytics.customer_segment s
            LEFT JOIN mart_customer.customer_base b
                ON s.customer_key = b.customer_key;
            """
        )

        conn.exec_driver_sql(
            """
            DROP TABLE IF EXISTS analytics.customer_territory_summary;

            CREATE TABLE analytics.customer_territory_summary AS
            SELECT
                b.territory_name,
                s.segment_name,
                COUNT(*) AS customer_count,
                SUM(COALESCE(b.revenue, 0)) AS total_revenue,
                SUM(COALESCE(b.estimated_gross_profit, 0)) AS total_gross_profit,
                AVG(COALESCE(b.estimated_gross_margin_pct, 0)) AS avg_gross_margin_pct
            FROM analytics.customer_segment s
            LEFT JOIN mart_customer.customer_base b
                ON s.customer_key = b.customer_key
            GROUP BY b.territory_name, s.segment_name;
            """
        )

def run_customer_segmentation(n_clusters: int = SELECTED_K) -> pd.DataFrame:
    ensure_analytics_schema()
    db_engine = engine()

    customers = pd.read_sql(
        "select * from analytics.feature_customer_rfm",
        db_engine,
    )
    values = customers[FEATURES].fillna(0)

    evaluation = []

    for k in K_RANGE:
        pipeline = build_pipeline(k)
        labels = pipeline.fit_predict(values)
        scaled = pipeline.named_steps["scale"].transform(values)

        evaluation.append(
            {
                "k": k,
                "silhouette_score": silhouette_score(scaled, labels),
                "inertia": pipeline.named_steps["model"].inertia_,
            }
        )

    evaluation_df = pd.DataFrame(evaluation)

    selected_k = n_clusters

    pipeline = build_pipeline(selected_k)
    labels = pipeline.fit_predict(values)
    scaled = pipeline.named_steps["scale"].transform(values)

    customers["segment_id"] = labels

    score = silhouette_score(scaled, labels)
    inertia = pipeline.named_steps["model"].inertia_

    profile = (
        customers.groupby("segment_id")
        .agg(
            customer_count=("customer_key", "count"),
            avg_recency=("recency_days", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            avg_aov=("average_order_value", "mean"),
            total_revenue=("monetary", "sum"),
        )
        .reset_index()
    )

    profile["segment_name"] = ""

    # 1. High Value -> Monetary cao nhất
    high_value_id = profile.loc[
        profile["avg_monetary"].idxmax(),
        "segment_id",
    ]

    profile.loc[
        profile["segment_id"] == high_value_id,
        "segment_name",
    ] = "high_value"

    # 2. Loyal -> Frequency cao nhất (không phải High Value)
    remaining = profile[
        profile["segment_id"] != high_value_id
    ]

    loyal_id = remaining.loc[
        remaining["avg_frequency"].idxmax(),
        "segment_id",
    ]

    profile.loc[
        profile["segment_id"] == loyal_id,
        "segment_name",
    ] = "loyal"

    # 3. At Risk -> Recency cao nhất
    remaining = profile[
        ~profile["segment_id"].isin(
            [high_value_id, loyal_id]
        )
    ]

    at_risk_id = remaining.loc[
        remaining["avg_recency"].idxmax(),
        "segment_id",
    ]

    profile.loc[
        profile["segment_id"] == at_risk_id,
        "segment_name",
    ] = "at_risk"

    # 4. Low Value -> Monetary thấp nhất trong các cluster còn lại
    remaining = profile[
        ~profile["segment_id"].isin(
            [high_value_id, loyal_id, at_risk_id]
        )
    ]

    low_value_id = remaining.loc[
        remaining["avg_monetary"].idxmin(),
        "segment_id",
    ]

    profile.loc[
        profile["segment_id"] == low_value_id,
        "segment_name",
    ] = "low_value"

    # 5. Cluster còn lại -> Developing
    remaining = profile[
        profile["segment_name"] == ""
    ]

    developing_id = remaining.iloc[0]["segment_id"]

    profile.loc[
        profile["segment_id"] == developing_id,
        "segment_name",
    ] = "developing"

    # Gắn tên segment vào từng khách hàng
    customers = customers.merge(
        profile[
            [
                "segment_id",
                "segment_name",
            ]
        ],
        on="segment_id",
        how="left",
    )

    customers["model_name"] = "rfm_kmeans"
    customers["model_version"] = "rfm_kmeans_v1"
    customers["selected_k"] = selected_k
    customers["silhouette_score"] = score
    customers["scored_at"] = pd.Timestamp.now(tz="UTC")

    profile["model_name"] = "rfm_kmeans"
    profile["model_version"] = "rfm_kmeans_v1"
    profile["selected_k"] = selected_k
    profile["silhouette_score"] = score
    profile["scored_at"] = pd.Timestamp.now(tz="UTC")

    configure_mlflow("customer_segmentation")

    with mlflow.start_run():
        mlflow.log_param("selected_k", selected_k)
        mlflow.log_param("features", ",".join(FEATURES))
        mlflow.log_metric("silhouette_score", score)
        mlflow.log_metric("inertia", inertia)
        mlflow.sklearn.log_model(pipeline, "model")

    customers.to_sql(
        "customer_segment",
        db_engine,
        schema="analytics",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )

    profile.to_sql(
        "customer_segment_profile",
        db_engine,
        schema="analytics",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )

    evaluation_df.to_sql(
        "customer_segmentation_metrics",
        db_engine,
        schema="analytics",
        if_exists="replace",
        index=False,
    )

    build_customer_analytics_tables(db_engine)

    print("Customer segmentation completed.")
    print(f"Selected k = {selected_k}")
    print(f"Silhouette score = {score:.4f}")
    print(f"Segmented {len(customers)} customers.")
    print(evaluation_df)

    return customers


if __name__ == "__main__":
    run_customer_segmentation()