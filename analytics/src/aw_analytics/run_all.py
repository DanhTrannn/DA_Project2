import os

from aw_analytics.forecasting import run_sales_forecast
from aw_analytics.market_basket import run_market_basket
from aw_analytics.segmentation import run_customer_segmentation


def run_all() -> None:
    if os.getenv("ENABLE_DATA_MINING", "false").lower() != "true":
        raise RuntimeError(
            "Data Mining is scaffold-only. Set ENABLE_DATA_MINING=true after "
            "the Data Mart and feature contracts have been reviewed."
        )
    run_customer_segmentation()
    run_market_basket()
    run_sales_forecast()


if __name__ == "__main__":
    run_all()
