from __future__ import annotations

import json
import os
import http.cookiejar
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


BASE_URL = os.getenv("SUPERSET_URL", "http://localhost:8088").rstrip("/")
USERNAME = os.getenv("SUPERSET_ADMIN_USER", "admin")
PASSWORD = os.getenv("SUPERSET_ADMIN_PASSWORD", "admin")
DATABASE_NAME = os.getenv("SUPERSET_SOURCE_DATABASE_NAME", "Adventureworks")
DASHBOARD_TITLE = "ADVENTURE WORKS CYCLE | Phân tích kinh doanh"
DASHBOARD_SLUG = "adventureworks-tv4-executive-data-quality"
DASHBOARD_CSS = """
.dashboard-content {
  background: #f8d8d2 !important;
  padding: 18px !important;
}

.dashboard-header {
  background: #f6c5c0 !important;
  border-bottom: 1px solid #dca8a2 !important;
}

.dashboard-component-chart-holder {
  background: #fffafa !important;
  border: 1px solid #edc9c4 !important;
  border-radius: 8px !important;
  box-shadow: 0 2px 8px rgba(105, 71, 68, 0.08) !important;
  overflow: hidden !important;
}

.dashboard-component-chart-holder .chart-header {
  background: #fffafa !important;
  color: #4f3633 !important;
  font-weight: 600 !important;
  min-height: 34px !important;
}

.dashboard-component-chart-holder .chart-container {
  padding: 4px 8px 10px !important;
}

.dashboard-component-row {
  margin-bottom: 12px !important;
}

.dashboard-component-chart-holder:hover {
  border-color: #cf928a !important;
  box-shadow: 0 4px 12px rgba(105, 71, 68, 0.14) !important;
}

.dashboard-markdown {
  background: transparent !important;
  color: #5d3e3a !important;
}
"""


class SupersetClient:
    def __init__(self) -> None:
        self.access_token = ""
        self.csrf_token = ""
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if self.csrf_token and method in {"POST", "PUT", "DELETE"}:
            headers["X-CSRFToken"] = self.csrf_token
        request = urllib.request.Request(
            f"{BASE_URL}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with self.opener.open(request, timeout=60) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Superset {method} {path} failed: {exc.code} {body}") from exc
        return json.loads(body) if body else {}

    def login(self) -> None:
        response = self.request(
            "POST",
            "/api/v1/security/login",
            {
                "username": USERNAME,
                "password": PASSWORD,
                "provider": "db",
                "refresh": True,
            },
        )
        self.access_token = response["access_token"]
        csrf_response = self.request("GET", "/api/v1/security/csrf_token/")
        self.csrf_token = csrf_response["result"]

    def list_all(self, resource: str) -> list[dict[str, Any]]:
        query = urllib.parse.urlencode({"q": "(page:0,page_size:1000)"})
        response = self.request("GET", f"/api/v1/{resource}/?{query}")
        return response.get("result", [])


def simple_metric(column_name: str, label: str, aggregate: str = "SUM") -> dict[str, Any]:
    return {
        "aggregate": aggregate,
        "column": {"column_name": column_name, "type": "NUMERIC"},
        "expressionType": "SIMPLE",
        "label": label,
        "optionName": f"metric_{column_name}_{aggregate.lower()}",
    }


def sql_metric(expression: str, label: str, option_name: str) -> dict[str, Any]:
    return {
        "expressionType": "SQL",
        "sqlExpression": expression,
        "label": label,
        "optionName": option_name,
    }


def sql_filter(expression: str, clause: str) -> dict[str, Any]:
    return {
        "clause": "WHERE",
        "comparator": expression,
        "expressionType": "SQL",
        "filterOptionName": clause,
        "fromFormData": True,
        "sqlExpression": expression,
        "subject": None,
    }


def numeric_filter(
    column_name: str,
    operator: str,
    comparator: int | float,
    option_name: str,
) -> dict[str, Any]:
    return {
        "clause": "WHERE",
        "comparator": comparator,
        "expressionType": "SIMPLE",
        "filterOptionName": option_name,
        "operator": operator,
        "sqlExpression": None,
        "subject": column_name,
    }


def get_database_id(client: SupersetClient) -> int:
    for database in client.list_all("database"):
        if database.get("database_name") == DATABASE_NAME:
            return int(database["id"])
    raise RuntimeError(f"Superset database not found: {DATABASE_NAME}")


def get_or_create_dataset(
    client: SupersetClient,
    database_id: int,
    schema: str,
    table_name: str,
) -> int:
    for dataset in client.list_all("dataset"):
        database = dataset.get("database") or {}
        if (
            dataset.get("schema") == schema
            and dataset.get("table_name") == table_name
            and (database.get("id") in {None, database_id})
        ):
            dataset_id = int(dataset["id"])
            client.request("PUT", f"/api/v1/dataset/{dataset_id}/refresh")
            return dataset_id
    response = client.request(
        "POST",
        "/api/v1/dataset/",
        {
            "database": database_id,
            "schema": schema,
            "table_name": table_name,
            "normalize_columns": True,
        },
    )
    return int(response["id"])


def get_or_create_dashboard(client: SupersetClient) -> int:
    for dashboard in client.list_all("dashboard"):
        title = str(dashboard.get("dashboard_title") or "")
        if title == DASHBOARD_TITLE or title.startswith("AdventureWorks TV4 - Executive"):
            return int(dashboard["id"])
    response = client.request(
        "POST",
        "/api/v1/dashboard/",
        {
            "dashboard_title": DASHBOARD_TITLE,
            "slug": DASHBOARD_SLUG,
            "published": True,
            "css": DASHBOARD_CSS,
            "json_metadata": json.dumps({}),
            "position_json": json.dumps({}),
        },
    )
    return int(response["id"])


def get_or_create_chart(
    client: SupersetClient,
    dashboard_id: int,
    dataset_id: int,
    slice_name: str,
    viz_type: str,
    params: dict[str, Any],
) -> int:
    payload = {
        "slice_name": slice_name,
        "viz_type": viz_type,
        "datasource_id": dataset_id,
        "datasource_type": "table",
        "params": json.dumps(params),
        "dashboards": [dashboard_id],
    }
    for chart in client.list_all("chart"):
        if chart.get("slice_name") == slice_name:
            chart_id = int(chart["id"])
            client.request("PUT", f"/api/v1/chart/{chart_id}", payload)
            return chart_id
    response = client.request("POST", "/api/v1/chart/", payload)
    return int(response["id"])


def remove_stale_dashboard_charts(
    client: SupersetClient,
    dashboard_id: int,
    keep_ids: set[int],
) -> None:
    for chart in client.list_all("chart"):
        owner_ids = {
            int(dashboard["id"])
            for dashboard in chart.get("dashboards") or []
            if dashboard.get("id") is not None
        }
        chart_id = int(chart["id"])
        if dashboard_id in owner_ids and chart_id not in keep_ids:
            client.request("DELETE", f"/api/v1/chart/{chart_id}")


def dashboard_layout(charts: list[tuple[int, str]]) -> str:
    root_id = "ROOT_ID"
    grid_id = "GRID_ID"
    tabs_id = "TABS-MAIN"
    layout: dict[str, Any] = {
        "DASHBOARD_VERSION_KEY": "v2",
        root_id: {"id": root_id, "type": "ROOT", "children": [grid_id]},
        grid_id: {
            "id": grid_id,
            "type": "GRID",
            "children": [tabs_id],
            "parents": [root_id],
        },
        tabs_id: {
            "id": tabs_id,
            "type": "TABS",
            "children": [],
            "meta": {},
            "parents": [root_id, grid_id],
        },
    }
    tabs = [
        (
            "OVERVIEW",
            "Tổng quan",
            [
                ([0, 1, 2, 3], 12),
                ([4, 5, 6, 7], 12),
                ([9, 10, 11], 30),
                ([12, 13], 36),
                ([14], 30),
                ([15, 16], 34),
            ],
        ),
        (
            "PRODUCT",
            "Sản phẩm",
            [([8, 17], 34), ([18, 19], 34)],
        ),
        (
            "CUSTOMER",
            "Khách hàng",
            [([20, 21], 34), ([22, 23], 34)],
        ),
    ]

    row_number = 0
    for tab_key, tab_label, rows in tabs:
        tab_id = f"TAB-{tab_key}"
        layout[tabs_id]["children"].append(tab_id)
        layout[tab_id] = {
            "id": tab_id,
            "type": "TAB",
            "children": [],
            "meta": {"text": tab_label},
            "parents": [root_id, grid_id, tabs_id],
        }

        for chart_indexes, height in rows:
            row_number += 1
            row_id = f"ROW-{row_number}"
            row_charts = [charts[index] for index in chart_indexes]
            chart_nodes = [f"CHART-{chart_id}" for chart_id, _ in row_charts]
            layout[tab_id]["children"].append(row_id)
            layout[row_id] = {
                "id": row_id,
                "type": "ROW",
                "children": chart_nodes,
                "meta": {"background": "BACKGROUND_TRANSPARENT"},
                "parents": [root_id, grid_id, tabs_id, tab_id],
            }
            width = 12 // len(row_charts)
            for chart_id, slice_name in row_charts:
                node_id = f"CHART-{chart_id}"
                layout[node_id] = {
                    "id": node_id,
                    "type": "CHART",
                    "children": [],
                    "meta": {
                        "chartId": chart_id,
                        "height": height,
                        "width": width,
                        "sliceName": slice_name,
                    },
                    "parents": [root_id, grid_id, tabs_id, tab_id, row_id],
                }
    return json.dumps(layout)


def main() -> None:
    client = SupersetClient()
    client.login()
    database_id = get_database_id(client)

    datasets = {
        "executive": get_or_create_dataset(client, database_id, "mart_sales", "executive_kpi"),
        "monthly": get_or_create_dataset(client, database_id, "mart_sales", "sales_monthly_kpi"),
        "pnl_monthly": get_or_create_dataset(
            client, database_id, "mart_finance", "management_pnl_monthly"
        ),
        "pnl": get_or_create_dataset(
            client, database_id, "mart_finance", "management_pnl_summary"
        ),
        "customer": get_or_create_dataset(
            client, database_id, "mart_customer", "customer_base"
        ),
        "product": get_or_create_dataset(
            client, database_id, "mart_product", "product_sales_summary"
        ),
        "sales_eda": get_or_create_dataset(
            client, database_id, "mart_sales_forecast", "monthly_sales_eda"
        ),
        "reconciliation": get_or_create_dataset(
            client, database_id, "audit", "source_to_dw_reconciliation"
        ),
        "quality": get_or_create_dataset(client, database_id, "audit", "data_quality_summary"),
    }
    dashboard_id = get_or_create_dashboard(client)
    complete_month_filter = sql_filter(
        "is_complete_month = TRUE",
        "executive_complete_months",
    )
    positive_revenue_filter = numeric_filter(
        "revenue",
        ">",
        0,
        "executive_positive_revenue",
    )

    chart_specs = [
        (
            datasets["executive"],
            "Tổng doanh thu",
            "big_number_total",
            {
                "datasource": f"{datasets['executive']}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric("revenue", "Doanh thu"),
                "adhoc_filters": [],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["executive"],
            "Lợi nhuận gộp ước tính",
            "big_number_total",
            {
                "datasource": f"{datasets['executive']}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric(
                    "estimated_gross_profit", "Lợi nhuận gộp ước tính"
                ),
                "adhoc_filters": [],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["pnl_monthly"],
            "Tổng phí vận chuyển",
            "big_number_total",
            {
                "datasource": f"{datasets['pnl_monthly']}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric("freight_amount", "Phí vận chuyển"),
                "adhoc_filters": [],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["customer"],
            "Tổng số khách hàng",
            "big_number_total",
            {
                "datasource": f"{datasets['customer']}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric("customer_key", "Số khách hàng", "COUNT"),
                "adhoc_filters": [],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["executive"],
            "Tổng số lượng bán",
            "big_number_total",
            {
                "datasource": f"{datasets['executive']}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric("quantity_sold", "Số lượng bán"),
                "adhoc_filters": [],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["executive"],
            "Biên lợi nhuận gộp ước tính",
            "big_number_total",
            {
                "datasource": f"{datasets['executive']}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric(
                    "estimated_gross_margin_pct", "Biên lợi nhuận gộp", "MAX"
                ),
                "adhoc_filters": [],
                "time_range": "No filter",
                "y_axis_format": ".1%",
            },
        ),
        (
            datasets["executive"],
            "Tổng số đơn hàng",
            "big_number_total",
            {
                "datasource": f"{datasets['executive']}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric("order_count", "Số đơn hàng"),
                "adhoc_filters": [],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["executive"],
            "Giá trị bán dưới giá vốn",
            "big_number_total",
            {
                "datasource": f"{datasets['executive']}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric("loss_amount", "Giá trị lỗ"),
                "adhoc_filters": [],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["product"],
            "Top 10 sản phẩm theo doanh thu",
            "echarts_timeseries_bar",
            {
                "datasource": f"{datasets['product']}__table",
                "viz_type": "echarts_timeseries_bar",
                "x_axis": "product_name",
                "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": [],
                "adhoc_filters": [positive_revenue_filter],
                "row_limit": 10,
                "order_desc": True,
                "x_axis_sort": "value",
                "x_axis_sort_asc": False,
                "orientation": "horizontal",
                "show_value": True,
                "show_legend": False,
                "truncate_metric": True,
                "y_axis_format": "SMART_NUMBER",
                "time_range": "No filter",
            },
        ),
        (
            datasets["sales_eda"],
            "Doanh thu theo quý",
            "echarts_timeseries_bar",
            {
                "datasource": f"{datasets['sales_eda']}__table",
                "viz_type": "echarts_timeseries_bar",
                "x_axis": "month",
                "time_grain_sqla": "P3M",
                "time_range": "No filter",
                "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": [],
                "adhoc_filters": [complete_month_filter],
                "show_value": True,
                "show_legend": False,
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["monthly"],
            "Doanh thu theo quốc gia",
            "echarts_timeseries_bar",
            {
                "datasource": f"{datasets['monthly']}__table",
                "viz_type": "echarts_timeseries_bar",
                "x_axis": "country_code",
                "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": [],
                "adhoc_filters": [],
                "row_limit": 10,
                "order_desc": True,
                "x_axis_sort": "value",
                "x_axis_sort_asc": False,
                "orientation": "horizontal",
                "show_value": True,
                "show_legend": False,
                "y_axis_format": "SMART_NUMBER",
                "time_range": "No filter",
            },
        ),
        (
            datasets["sales_eda"],
            "Doanh thu theo năm",
            "echarts_timeseries_bar",
            {
                "datasource": f"{datasets['sales_eda']}__table",
                "viz_type": "echarts_timeseries_bar",
                "x_axis": "month",
                "time_grain_sqla": "P1Y",
                "time_range": "No filter",
                "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": [],
                "adhoc_filters": [complete_month_filter],
                "show_value": True,
                "show_legend": False,
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["sales_eda"],
            "Doanh thu, giá vốn và lợi nhuận gộp theo tháng",
            "echarts_timeseries_bar",
            {
                "datasource": f"{datasets['sales_eda']}__table",
                "viz_type": "echarts_timeseries_bar",
                "x_axis": "month",
                "time_grain_sqla": "P1M",
                "time_range": "No filter",
                "metrics": [
                    simple_metric("revenue", "Doanh thu"),
                    simple_metric("estimated_cogs", "Giá vốn ước tính"),
                    simple_metric(
                        "estimated_gross_profit", "Lợi nhuận gộp ước tính"
                    ),
                ],
                "groupby": [],
                "adhoc_filters": [complete_month_filter],
                "show_value": False,
                "show_legend": True,
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["sales_eda"],
            "Xu hướng doanh thu theo tháng",
            "echarts_timeseries_line",
            {
                "datasource": f"{datasets['sales_eda']}__table",
                "viz_type": "echarts_timeseries_line",
                "x_axis": "month",
                "time_grain_sqla": "P1M",
                "time_range": "No filter",
                "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": [],
                "adhoc_filters": [complete_month_filter],
                "show_value": True,
                "show_legend": False,
                "rich_tooltip": True,
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["pnl"],
            "Từ doanh thu đến lợi nhuận gộp",
            "echarts_timeseries_bar",
            {
                "datasource": f"{datasets['pnl']}__table",
                "viz_type": "echarts_timeseries_bar",
                "x_axis": "line_item",
                "metrics": [simple_metric("amount", "Giá trị")],
                "groupby": [],
                "adhoc_filters": [],
                "row_limit": 10,
                "orientation": "horizontal",
                "show_value": True,
                "show_legend": False,
                "y_axis_format": "SMART_NUMBER",
                "time_range": "No filter",
            },
        ),
        (
            datasets["reconciliation"],
            "Đối soát OLTP và Kho Dữ Liệu",
            "table",
            {
                "datasource": f"{datasets['reconciliation']}__table",
                "viz_type": "table",
                "query_mode": "raw",
                "all_columns": [
                    "metric_name",
                    "source_value",
                    "dw_value",
                    "difference",
                    "status",
                ],
                "adhoc_filters": [],
                "row_limit": 100,
            },
        ),
        (
            datasets["quality"],
            "Kiểm tra chất lượng dữ liệu",
            "table",
            {
                "datasource": f"{datasets['quality']}__table",
                "viz_type": "table",
                "query_mode": "raw",
                "all_columns": [
                    "model_name",
                    "check_name",
                    "failed_record_count",
                    "status",
                ],
                "adhoc_filters": [],
                "row_limit": 100,
            },
        ),
        (
            datasets["product"],
            "Cơ cấu doanh thu theo danh mục sản phẩm",
            "pie",
            {
                "datasource": f"{datasets['product']}__table",
                "viz_type": "pie",
                "metric": simple_metric("revenue", "Doanh thu"),
                "groupby": ["product_category_name"],
                "adhoc_filters": [positive_revenue_filter],
                "row_limit": 10,
                "order_desc": True,
                "donut": True,
                "show_labels": True,
                "show_legend": True,
                "label_type": "key_percent",
                "number_format": "SMART_NUMBER",
                "time_range": "No filter",
            },
        ),
        (
            datasets["product"],
            "Ma trận hiệu quả sản phẩm",
            "bubble_v2",
            {
                "datasource": f"{datasets['product']}__table",
                "viz_type": "bubble_v2",
                "entity": "product_name",
                "series": "product_category_name",
                "x": simple_metric("revenue", "Doanh thu"),
                "y": simple_metric(
                    "estimated_gross_margin_pct",
                    "Biên lợi nhuận gộp ước tính",
                    "AVG",
                ),
                "size": simple_metric("quantity_sold", "Số lượng bán"),
                "adhoc_filters": [positive_revenue_filter],
                "row_limit": 100,
                "order_desc": True,
                "max_bubble_size": "50",
                "show_legend": True,
                "xAxisFormat": "SMART_NUMBER",
                "yAxisFormat": ".1%",
                "time_range": "No filter",
            },
        ),
        (
            datasets["product"],
            "Top 10 sản phẩm gây lỗ gộp",
            "echarts_timeseries_bar",
            {
                "datasource": f"{datasets['product']}__table",
                "viz_type": "echarts_timeseries_bar",
                "x_axis": "product_name",
                "metrics": [simple_metric("loss_amount", "Giá trị lỗ")],
                "groupby": [],
                "adhoc_filters": [
                    positive_revenue_filter,
                    numeric_filter(
                        "estimated_gross_profit",
                        "<",
                        0,
                        "executive_loss_products",
                    ),
                ],
                "row_limit": 10,
                "order_desc": True,
                "x_axis_sort": "value",
                "x_axis_sort_asc": False,
                "orientation": "horizontal",
                "show_value": True,
                "show_legend": False,
                "truncate_metric": True,
                "y_axis_format": "SMART_NUMBER",
                "time_range": "No filter",
            },
        ),
        (
            datasets["customer"],
            "Top 10 khách hàng theo doanh thu",
            "echarts_timeseries_bar",
            {
                "datasource": f"{datasets['customer']}__table",
                "viz_type": "echarts_timeseries_bar",
                "x_axis": "customer_name",
                "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": [],
                "adhoc_filters": [positive_revenue_filter],
                "row_limit": 10,
                "order_desc": True,
                "x_axis_sort": "value",
                "x_axis_sort_asc": False,
                "orientation": "horizontal",
                "show_value": True,
                "show_legend": False,
                "truncate_metric": True,
                "y_axis_format": "SMART_NUMBER",
                "time_range": "No filter",
            },
        ),
        (
            datasets["customer"],
            "Bản đồ nhiệt doanh thu theo loại khách hàng và khu vực",
            "heatmap_v2",
            {
                "datasource": f"{datasets['customer']}__table",
                "viz_type": "heatmap_v2",
                "x_axis": "customer_type",
                "groupby": ["territory_name"],
                "metric": simple_metric("revenue", "Doanh thu"),
                "adhoc_filters": [
                    positive_revenue_filter,
                    sql_filter(
                        "territory_name IS NOT NULL",
                        "executive_customer_heatmap_territory",
                    ),
                ],
                "row_limit": 1000,
                "show_legend": True,
                "show_values": True,
                "normalize_across": "heatmap",
                "linear_color_scheme": "blue_white_yellow",
                "y_axis_format": "SMART_NUMBER",
                "time_range": "No filter",
            },
        ),
        (
            datasets["customer"],
            "Doanh thu khách hàng theo khu vực",
            "echarts_timeseries_bar",
            {
                "datasource": f"{datasets['customer']}__table",
                "viz_type": "echarts_timeseries_bar",
                "x_axis": "territory_name",
                "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": [],
                "adhoc_filters": [
                    positive_revenue_filter,
                    sql_filter(
                        "territory_name IS NOT NULL",
                        "executive_customer_territory",
                    ),
                ],
                "row_limit": 10,
                "order_desc": True,
                "x_axis_sort": "value",
                "x_axis_sort_asc": False,
                "orientation": "horizontal",
                "show_value": True,
                "show_legend": False,
                "y_axis_format": "SMART_NUMBER",
                "time_range": "No filter",
            },
        ),
        (
            datasets["customer"],
            "Top 10 khách hàng theo giá trị đơn hàng trung bình",
            "echarts_timeseries_bar",
            {
                "datasource": f"{datasets['customer']}__table",
                "viz_type": "echarts_timeseries_bar",
                "x_axis": "customer_name",
                "metrics": [
                    simple_metric("average_order_value", "Giá trị đơn hàng trung bình")
                ],
                "groupby": [],
                "adhoc_filters": [positive_revenue_filter],
                "row_limit": 10,
                "order_desc": True,
                "x_axis_sort": "value",
                "x_axis_sort_asc": False,
                "orientation": "horizontal",
                "show_value": True,
                "show_legend": False,
                "truncate_metric": True,
                "y_axis_format": "SMART_NUMBER",
                "time_range": "No filter",
            },
        ),
    ]

    charts: list[tuple[int, str]] = []
    for dataset_id, slice_name, viz_type, params in chart_specs:
        chart_id = get_or_create_chart(
            client,
            dashboard_id,
            dataset_id,
            slice_name,
            viz_type,
            params,
        )
        charts.append((chart_id, slice_name))

    remove_stale_dashboard_charts(
        client,
        dashboard_id,
        {chart_id for chart_id, _ in charts},
    )

    client.request(
        "PUT",
        f"/api/v1/dashboard/{dashboard_id}",
        {
            "dashboard_title": DASHBOARD_TITLE,
            "slug": DASHBOARD_SLUG,
            "published": True,
            "css": DASHBOARD_CSS,
            "position_json": dashboard_layout(charts),
            "json_metadata": json.dumps(
                {
                    "timed_refresh_immune_slices": [],
                    "expanded_slices": {},
                    "refresh_frequency": 0,
                    "color_scheme": "bnbColors",
                    "label_colors": {
                        "Doanh thu": "#c89078",
                        "Giá vốn ước tính": "#8fa9c4",
                        "Lợi nhuận gộp ước tính": "#b89a54",
                    },
                }
            ),
        },
    )
    print(
        f"Dashboard ready: {BASE_URL}/superset/dashboard/{DASHBOARD_SLUG}/"
    )


if __name__ == "__main__":
    main()
