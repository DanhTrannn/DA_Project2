from __future__ import annotations

import os

import mlflow
import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth

from aw_analytics.db import engine, ensure_analytics_schema
from aw_analytics.tracking import configure_mlflow


def run_market_basket(min_support: float | None = None) -> pd.DataFrame:
    ensure_analytics_schema()
    min_support = min_support or float(os.getenv("MARKET_BASKET_MIN_SUPPORT", "0.01"))
    db_engine = engine()
    lines = pd.read_sql(
        """
        select d.sales_order_id, p.product_name
        from staging.stg_sales_order_detail d
        join staging.stg_product p using (product_id)
        """,
        db_engine,
    )
    basket = (
        lines.assign(present=1)
        .drop_duplicates()
        .pivot(index="sales_order_id", columns="product_name", values="present")
        .fillna(0)
        .astype(bool)
    )
    itemsets = fpgrowth(basket, min_support=min_support, use_colnames=True)
    if itemsets.empty:
        rules = pd.DataFrame()
    else:
        rules = association_rules(itemsets, metric="lift", min_threshold=1.0)

    if rules.empty:
        output = pd.DataFrame(
            columns=["antecedents", "consequents", "support", "confidence", "lift", "scored_at"]
        )
    else:
        output = rules[["antecedents", "consequents", "support", "confidence", "lift"]].copy()
        output["antecedents"] = output["antecedents"].map(lambda value: " + ".join(sorted(value)))
        output["consequents"] = output["consequents"].map(lambda value: " + ".join(sorted(value)))
        output = output[
            (output["support"] >= 0.01) &
            (output["confidence"] >= 0.50) &
            (output["lift"] >= 1.20)
        ]
        output = output.sort_values(["lift", "confidence", "support"], ascending=False)        
        output["scored_at"] = pd.Timestamp.now(tz="UTC")

    configure_mlflow("market_basket")
    with mlflow.start_run():
        mlflow.log_param("algorithm", "fp_growth")
        mlflow.log_param("min_support", min_support)
        mlflow.log_metric("transactions", len(basket))
        mlflow.log_metric("rules", len(output))

    output.to_sql(
        "product_association_rules",
        db_engine,
        schema="analytics",
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )
    return output


if __name__ == "__main__":
    result = run_market_basket()
    print(f"Generated {len(result)} product association rules.")
