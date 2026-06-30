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
DASHBOARD_TITLE = "AdventureWorks TV4 - Executive & Data Quality"
DASHBOARD_SLUG = "adventureworks-tv4-executive-data-quality"


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
    layout: dict[str, Any] = {
        "DASHBOARD_VERSION_KEY": "v2",
        root_id: {"id": root_id, "type": "ROOT", "children": [grid_id]},
        grid_id: {
            "id": grid_id,
            "type": "GRID",
            "children": [],
            "parents": [root_id],
        },
    }
    sections = [
        (
            "01. Tổng quan điều hành",
            "Quy mô bán hàng, lợi nhuận gộp và phần giá trị bị bào mòn bởi các dòng bán dưới giá vốn.",
            [[0, 1, 2], [3, 4]],
            14,
        ),
        (
            "02. Hiệu quả tài chính",
            "Theo dõi doanh thu và lợi nhuận gộp theo thời gian; P&L chỉ phản ánh gross-level vì nguồn không có đầy đủ chi phí hoạt động, nợ và dòng tiền.",
            [[5], [6]],
            38,
        ),
        (
            "03. Chất lượng và đối soát dữ liệu",
            "Các chỉ tiêu nguồn và DW phải khớp; kiểm tra chất lượng không được có trạng thái FAIL.",
            [[7, 8]],
            42,
        ),
    ]

    row_number = 0
    for section_number, (title, description, rows, height) in enumerate(sections, 1):
        markdown_id = f"MARKDOWN-{section_number}"
        layout[grid_id]["children"].append(markdown_id)
        layout[markdown_id] = {
            "id": markdown_id,
            "type": "MARKDOWN",
            "children": [],
            "meta": {
                "code": f"## {title}\n{description}",
                "height": 7,
                "width": 12,
            },
            "parents": [root_id, grid_id],
        }
        for chart_indexes in rows:
            row_number += 1
            row_id = f"ROW-{row_number}"
            row_charts = [charts[index] for index in chart_indexes]
            chart_nodes = [f"CHART-{chart_id}" for chart_id, _ in row_charts]
            layout[grid_id]["children"].append(row_id)
            layout[row_id] = {
                "id": row_id,
                "type": "ROW",
                "children": chart_nodes,
                "meta": {"background": "BACKGROUND_TRANSPARENT"},
                "parents": [root_id, grid_id],
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
                    "parents": [root_id, grid_id, row_id],
                }
    return json.dumps(layout)


def main() -> None:
    client = SupersetClient()
    client.login()
    database_id = get_database_id(client)

    datasets = {
        "executive": get_or_create_dataset(client, database_id, "mart_sales", "executive_kpi"),
        "monthly": get_or_create_dataset(client, database_id, "mart_sales", "sales_monthly_kpi"),
        "pnl": get_or_create_dataset(
            client, database_id, "mart_finance", "management_pnl_summary"
        ),
        "reconciliation": get_or_create_dataset(
            client, database_id, "audit", "source_to_dw_reconciliation"
        ),
        "quality": get_or_create_dataset(client, database_id, "audit", "data_quality_summary"),
    }
    dashboard_id = get_or_create_dashboard(client)

    chart_specs = [
        (
            datasets["executive"],
            "TV4 | Quy mô | Tổng doanh thu AdventureWorks",
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
            "TV4 | Hiệu quả | Lợi nhuận gộp ước tính",
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
            datasets["executive"],
            "TV4 | Biên lợi nhuận | Tỷ lệ lợi nhuận gộp ước tính",
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
            "TV4 | Hoạt động | Tổng số đơn hàng",
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
            "TV4 | Rò rỉ lợi nhuận | Giá trị bán dưới giá vốn",
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
            datasets["monthly"],
            "TV4 | Xu hướng | Doanh thu và lợi nhuận gộp theo tháng",
            "echarts_timeseries_line",
            {
                "datasource": f"{datasets['monthly']}__table",
                "viz_type": "echarts_timeseries_line",
                "x_axis": "month",
                "time_grain_sqla": "P1M",
                "time_range": "No filter",
                "metrics": [
                    simple_metric("revenue", "Doanh thu"),
                    simple_metric(
                        "estimated_gross_profit", "Lợi nhuận gộp ước tính"
                    ),
                ],
                "groupby": [],
                "adhoc_filters": [],
                "show_legend": True,
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["pnl"],
            "TV4 | P&L gross-level | Doanh thu chuyển thành lợi nhuận gộp",
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
            "TV4 | Đối soát | Nguồn và Kho Dữ Liệu phải khớp",
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
            "TV4 | Chất lượng dữ liệu | Không được có kiểm tra FAIL",
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
            "position_json": dashboard_layout(charts),
            "json_metadata": json.dumps(
                {
                    "timed_refresh_immune_slices": [],
                    "expanded_slices": {},
                    "refresh_frequency": 0,
                    "color_scheme": "supersetColors",
                    "label_colors": {},
                }
            ),
        },
    )
    print(
        f"Dashboard ready: {BASE_URL}/superset/dashboard/{DASHBOARD_SLUG}/"
    )


if __name__ == "__main__":
    main()
