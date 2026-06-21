# Data Mining scaffold

This package contains prototype implementations for customer segmentation,
market-basket analysis, and sales forecasting. The staging-only Prefect
pipeline does not invoke them. They require reviewed Data Marts and feature
contracts before being enabled. Database access defaults to the AdventureWorks
OLTP service and uses the `SOURCE_*` environment variables.
