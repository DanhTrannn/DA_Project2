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


def run_customer_segmentation(n_clusters: int = 4) -> pd.DataFrame:
    ensure_analytics_schema()
    db_engine = engine()
    customers = pd.read_sql("select * from analytics.feature_customer_rfm", db_engine)
    values = customers[FEATURES].fillna(0)

    pipeline = Pipeline(
        [
            ("scale", StandardScaler()),
            ("model", KMeans(n_clusters=n_clusters, random_state=42, n_init=20)),
        ]
    )
    labels = pipeline.fit_predict(values)
    customers["segment_id"] = labels
    score = silhouette_score(pipeline.named_steps["scale"].transform(values), labels)

    segment_order = (
        customers.groupby("segment_id")["monetary"].mean().sort_values().index.tolist()
    )
    names = ["low_value", "developing", "loyal", "high_value"]
    segment_names = {
        segment_id: names[min(index, len(names) - 1)]
        for index, segment_id in enumerate(segment_order)
    }
    customers["segment_name"] = customers["segment_id"].map(segment_names)
    customers["model_name"] = "rfm_kmeans"
    customers["model_version"] = "1"
    customers["scored_at"] = pd.Timestamp.now(tz="UTC")

    configure_mlflow("customer_segmentation")
    with mlflow.start_run():
        mlflow.log_param("n_clusters", n_clusters)
        mlflow.log_param("features", ",".join(FEATURES))
        mlflow.log_metric("silhouette_score", score)
        mlflow.sklearn.log_model(pipeline, "model")

    customers.to_sql(
        "customer_segments",
        db_engine,
        schema="analytics",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )
    return customers


if __name__ == "__main__":
    result = run_customer_segmentation()
    print(f"Segmented {len(result)} customers.")
