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
DASHBOARD_TITLE = "AdventureWorks TV4 - Executive & Macro"


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
            return int(dataset["id"])
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
        if dashboard.get("dashboard_title") == DASHBOARD_TITLE:
            return int(dashboard["id"])
    response = client.request(
        "POST",
        "/api/v1/dashboard/",
        {
            "dashboard_title": DASHBOARD_TITLE,
            "slug": "adventureworks-tv4-executive-macro",
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
    for row_number in range(0, len(charts), 3):
        row_id = f"ROW-{row_number // 3 + 1}"
        row_charts = charts[row_number : row_number + 3]
        chart_nodes = [f"CHART-{chart_id}" for chart_id, _ in row_charts]
        layout[grid_id]["children"].append(row_id)
        layout[row_id] = {
            "id": row_id,
            "type": "ROW",
            "children": chart_nodes,
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": [root_id, grid_id],
        }
        for chart_id, slice_name in row_charts:
            node_id = f"CHART-{chart_id}"
            layout[node_id] = {
                "id": node_id,
                "type": "CHART",
                "children": [],
                "meta": {
                    "chartId": chart_id,
                    "height": 30,
                    "width": 4,
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
        "reconciliation": get_or_create_dataset(
            client, database_id, "audit", "source_to_dw_reconciliation"
        ),
        "quality": get_or_create_dataset(client, database_id, "audit", "data_quality_summary"),
        "macro": get_or_create_dataset(
            client, database_id, "mart_macro", "business_kpi_macro_period"
        ),
    }
    dashboard_id = get_or_create_dashboard(client)

    chart_specs = [
        (
            datasets["executive"],
            "TV4 - Revenue",
            "big_number_total",
            {
                "datasource": f"{datasets['executive']}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric("revenue", "Revenue"),
                "adhoc_filters": [],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["executive"],
            "TV4 - Estimated Gross Profit",
            "big_number_total",
            {
                "datasource": f"{datasets['executive']}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric("estimated_gross_profit", "Gross Profit"),
                "adhoc_filters": [],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["executive"],
            "TV4 - Gross Margin %",
            "big_number_total",
            {
                "datasource": f"{datasets['executive']}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric(
                    "estimated_gross_margin_pct", "Gross Margin %", "MAX"
                ),
                "adhoc_filters": [],
                "time_range": "No filter",
                "y_axis_format": ".2%",
            },
        ),
        (
            datasets["monthly"],
            "TV4 - Revenue Trend by Country",
            "echarts_timeseries_line",
            {
                "datasource": f"{datasets['monthly']}__table",
                "viz_type": "echarts_timeseries_line",
                "x_axis": "month",
                "time_grain_sqla": "P1M",
                "time_range": "No filter",
                "metrics": [simple_metric("revenue", "Revenue")],
                "groupby": ["country_code"],
                "adhoc_filters": [],
                "show_legend": True,
            },
        ),
        (
            datasets["reconciliation"],
            "TV4 - Source to DW Reconciliation",
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
            datasets["macro"],
            "TV4 - Macro Context by Country and Year",
            "table",
            {
                "datasource": f"{datasets['macro']}__table",
                "viz_type": "table",
                "query_mode": "raw",
                "all_columns": [
                    "country_code",
                    "year",
                    "revenue",
                    "estimated_gross_margin_pct",
                    "inflation_pct",
                    "gdp_growth_pct",
                    "unemployment_pct",
                    "macro_coverage_status",
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

    client.request(
        "PUT",
        f"/api/v1/dashboard/{dashboard_id}",
        {
            "dashboard_title": DASHBOARD_TITLE,
            "slug": "adventureworks-tv4-executive-macro",
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
        f"Dashboard ready: {BASE_URL}/superset/dashboard/"
        "adventureworks-tv4-executive-macro/"
    )


if __name__ == "__main__":
    main()
