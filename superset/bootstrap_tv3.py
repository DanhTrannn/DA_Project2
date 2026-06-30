from __future__ import annotations

import json
import os

import psycopg2

from bootstrap_tv4 import (
    BASE_URL,
    SupersetClient,
    get_database_id,
    get_or_create_dataset,
    simple_metric,
)


DASHBOARD_TITLE = "Phân tích khám phá doanh thu AdventureWorks"
DASHBOARD_SLUG = "adventureworks-tv3-sales-forecast"
LEGACY_DASHBOARD_TITLES = {"Phân tích và dự báo doanh thu AdventureWorks"}


def get_or_create_dashboard(client: SupersetClient) -> int:
    accepted_titles = {DASHBOARD_TITLE, *LEGACY_DASHBOARD_TITLES}
    for dashboard in client.list_all("dashboard"):
        if dashboard.get("dashboard_title") in accepted_titles:
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
    legacy_prefixes: tuple[str, ...],
    viz_type: str,
    params: dict[str, object],
) -> int:
    payload = {
        "slice_name": slice_name,
        "viz_type": viz_type,
        "datasource_id": dataset_id,
        "datasource_type": "table",
        "params": json.dumps(params),
        "dashboards": [dashboard_id],
    }
    prefixes = {
        f"{name.split('|', 1)[0].strip()} |"
        for name in (slice_name, *legacy_prefixes)
    }
    for chart in client.list_all("chart"):
        owner_ids = {
            int(dashboard["id"])
            for dashboard in chart.get("dashboards") or []
            if dashboard.get("id") is not None
        }
        if dashboard_id not in owner_ids:
            continue
        chart_name = str(chart.get("slice_name") or "")
        if any(chart_name.startswith(prefix) for prefix in prefixes):
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


def sql_filter(expression: str, name: str) -> dict[str, object]:
    return {
        "clause": "WHERE",
        "comparator": None,
        "expressionType": "SQL",
        "filterOptionName": name,
        "operator": None,
        "sqlExpression": expression,
        "subject": None,
    }


def sql_metric(expression: str, label: str, option_name: str) -> dict[str, object]:
    return {
        "expressionType": "SQL",
        "sqlExpression": expression,
        "label": label,
        "optionName": option_name,
    }


def money_millions(value: object, decimals: int = 2) -> str:
    amount = f"{float(value) / 1_000_000:.{decimals}f}".replace(".", ",")
    return f"{amount} triệu USD"


def percentage(value: object) -> str:
    return f"{float(value) * 100:.1f}".replace(".", ",") + "%"


def integer_vi(value: object) -> str:
    return f"{int(value):,}".replace(",", ".")


def load_story_metrics() -> dict[str, object]:
    source_uri = os.getenv("SUPERSET_SOURCE_URI")
    if not source_uri:
        raise RuntimeError("SUPERSET_SOURCE_URI is required to build TV3 EDA titles")

    query = """
        with monthly as (
            select *
            from mart_sales_forecast.monthly_sales_eda
            where is_complete_month
        ),
        bounds as (
            select max(month) as data_end from monthly
        ),
        peak_revenue as (
            select month, revenue
            from monthly
            order by revenue desc
            limit 1
        ),
        peak_profit as (
            select month, estimated_gross_profit
            from monthly
            order by estimated_gross_profit desc
            limit 1
        ),
        country as (
            select country_code, sum(revenue) as revenue
            from mart_sales.sales_monthly_kpi
            where month <= (select data_end from bounds)
            group by country_code
        ),
        top_country as (
            select
                country_code,
                revenue / nullif(sum(revenue) over (), 0) as revenue_share
            from country
            order by revenue desc
            limit 1
        ),
        seasonal_month as (
            select month_number, avg(revenue) as avg_revenue
            from monthly
            group by month_number
            order by avg_revenue desc
            limit 1
        )
        select
            min(m.month) as data_start,
            max(m.month) as data_end,
            sum(m.revenue) as total_revenue,
            sum(m.order_count) as total_orders,
            sum(m.quantity_sold) as total_units,
            sum(m.estimated_gross_profit) / nullif(sum(m.revenue), 0) as margin,
            (select month from peak_revenue) as peak_revenue_month,
            (select revenue from peak_revenue) as peak_revenue_value,
            (select month from peak_profit) as peak_profit_month,
            (select estimated_gross_profit from peak_profit) as peak_profit_value,
            avg(m.estimated_gross_margin_pct) as avg_margin,
            avg(m.estimated_gross_margin_pct) filter (
                where m.month > (select data_end from bounds) - interval '6 months'
            ) as recent_margin,
            (array_agg(m.month order by m.month desc))[1] as latest_yoy_month,
            (array_agg(m.revenue_yoy_growth_pct order by m.month desc))[1] as latest_yoy,
            (select country_code from top_country) as top_country,
            (select revenue_share from top_country) as top_country_share,
            (select month_number from seasonal_month) as strongest_calendar_month
        from monthly m
    """
    connection_uri = source_uri.replace("postgresql+psycopg2://", "postgresql://", 1)
    with psycopg2.connect(connection_uri) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()
            columns = [description.name for description in cursor.description]
    if row is None:
        raise RuntimeError("TV3 monthly EDA mart returned no metrics")
    return dict(zip(columns, row))


def story_titles(metrics: dict[str, object]) -> list[str]:
    data_start = metrics["data_start"]
    data_end = metrics["data_end"]
    peak_revenue_month = metrics["peak_revenue_month"]
    peak_profit_month = metrics["peak_profit_month"]
    latest_yoy_month = metrics["latest_yoy_month"]
    return [
        (
            f"Quy mô | Doanh thu {money_millions(metrics['total_revenue'], 1)} "
            f"trong {data_start:%m/%Y}-{data_end:%m/%Y}"
        ),
        f"Đơn hàng | {integer_vi(metrics['total_orders'])} đơn trong kỳ phân tích",
        f"Sản lượng | Đã bán {integer_vi(metrics['total_units'])} sản phẩm",
        f"Hiệu quả | Biên lợi nhuận gộp ước tính đạt {percentage(metrics['margin'])}",
        (
            f"Xu hướng doanh thu | Đỉnh {money_millions(metrics['peak_revenue_value'])} "
            f"vào {peak_revenue_month:%m/%Y}"
        ),
        (
            f"Lợi nhuận gộp | Đỉnh {money_millions(metrics['peak_profit_value'])} "
            f"vào {peak_profit_month:%m/%Y}"
        ),
        (
            f"Biên lợi nhuận | 6 tháng gần nhất {percentage(metrics['recent_margin'])}, "
            f"bình quân toàn kỳ {percentage(metrics['avg_margin'])}"
        ),
        (
            f"Thị trường | {metrics['top_country']} đóng góp "
            f"{percentage(metrics['top_country_share'])} doanh thu"
        ),
        (
            f"Tăng trưởng YoY | {latest_yoy_month:%m/%Y} đạt "
            f"{percentage(metrics['latest_yoy'])}"
        ),
        (
            "Mùa vụ | Tháng "
            f"{int(metrics['strongest_calendar_month']):02d} có doanh thu bình quân cao nhất"
        ),
    ]


def dashboard_layout(charts: list[tuple[int, str]]) -> str:
    if len(charts) != 10:
        raise ValueError(f"TV3 dashboard requires 10 charts, received {len(charts)}")
    root_id = "ROOT_ID"
    grid_id = "GRID_ID"
    layout: dict[str, object] = {
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
        [(charts[index], 3, 18) for index in range(4)],
        [(charts[4], 12, 34)],
        [(charts[5], 12, 34)],
        [(charts[6], 6, 32), (charts[7], 6, 32)],
        [(charts[8], 12, 34)],
        [(charts[9], 12, 38)],
    ]
    for row_number, section in enumerate(sections, start=1):
        row_id = f"ROW-{row_number}"
        layout[grid_id]["children"].append(row_id)  # type: ignore[index]
        layout[row_id] = {
            "id": row_id,
            "type": "ROW",
            "children": [f"CHART-{chart[0]}" for chart, _, _ in section],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": [root_id, grid_id],
        }
        for (chart_id, slice_name), width, height in section:
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


def time_chart_params(
    dataset_id: int,
    viz_type: str,
    metric: dict[str, object],
    y_axis_format: str = "SMART_NUMBER",
) -> dict[str, object]:
    return {
        "datasource": f"{dataset_id}__table",
        "viz_type": viz_type,
        "x_axis": "month",
        "time_grain_sqla": "P1M",
        "time_range": "No filter",
        "metrics": [metric],
        "groupby": [],
        "adhoc_filters": [sql_filter("is_complete_month = TRUE", "tv3_complete_months")],
        "show_legend": False,
        "show_value": False,
        "rich_tooltip": True,
        "y_axis_format": y_axis_format,
    }


def horizontal_bar_params(
    dataset_id: int,
    dimension: str,
    metric: dict[str, object],
) -> dict[str, object]:
    return {
        "datasource": f"{dataset_id}__table",
        "viz_type": "echarts_timeseries_bar",
        "x_axis": dimension,
        "metrics": [metric],
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
    }


def main() -> None:
    client = SupersetClient()
    client.login()
    database_id = get_database_id(client)
    datasets = {
        "eda": get_or_create_dataset(
            client,
            database_id,
            "mart_sales_forecast",
            "monthly_sales_eda",
        ),
        "country": get_or_create_dataset(
            client,
            database_id,
            "mart_sales",
            "sales_monthly_kpi",
        ),
    }
    dashboard_id = get_or_create_dashboard(client)
    story = load_story_metrics()
    titles = story_titles(story)
    complete_filter = sql_filter(
        f"month <= DATE '{story['data_end']:%Y-%m-%d}'",
        "tv3_country_complete_months",
    )

    chart_specs = [
        (
            datasets["eda"],
            titles[0],
            ("Hiện tại |",),
            "big_number_total",
            {
                "datasource": f"{datasets['eda']}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric("revenue", "Tổng doanh thu"),
                "adhoc_filters": [
                    sql_filter("is_complete_month = TRUE", "tv3_kpi_complete_months")
                ],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["eda"],
            titles[1],
            ("Dự báo |",),
            "big_number_total",
            {
                "datasource": f"{datasets['eda']}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric("order_count", "Tổng đơn hàng"),
                "adhoc_filters": [
                    sql_filter("is_complete_month = TRUE", "tv3_kpi_complete_months")
                ],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["eda"],
            titles[2],
            ("Tăng trưởng kỳ vọng |",),
            "big_number_total",
            {
                "datasource": f"{datasets['eda']}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric("quantity_sold", "Tổng số lượng bán"),
                "adhoc_filters": [
                    sql_filter("is_complete_month = TRUE", "tv3_kpi_complete_months")
                ],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            datasets["eda"],
            titles[3],
            ("Độ tin cậy |",),
            "big_number_total",
            {
                "datasource": f"{datasets['eda']}__table",
                "viz_type": "big_number_total",
                "metric": sql_metric(
                    "SUM(estimated_gross_profit) / NULLIF(SUM(revenue), 0)",
                    "Biên lợi nhuận gộp ước tính",
                    "metric_tv3_weighted_margin",
                ),
                "adhoc_filters": [
                    sql_filter("is_complete_month = TRUE", "tv3_kpi_complete_months")
                ],
                "time_range": "No filter",
                "y_axis_format": ".1%",
            },
        ),
        (
            datasets["eda"],
            titles[4],
            (),
            "echarts_timeseries_line",
            time_chart_params(
                datasets["eda"],
                "echarts_timeseries_line",
                simple_metric("revenue", "Doanh thu"),
            ),
        ),
        (
            datasets["eda"],
            titles[5],
            (),
            "echarts_timeseries_bar",
            time_chart_params(
                datasets["eda"],
                "echarts_timeseries_bar",
                simple_metric("estimated_gross_profit", "Lợi nhuận gộp ước tính"),
            ),
        ),
        (
            datasets["eda"],
            titles[6],
            (),
            "echarts_timeseries_line",
            time_chart_params(
                datasets["eda"],
                "echarts_timeseries_line",
                simple_metric(
                    "estimated_gross_margin_pct",
                    "Biên lợi nhuận gộp ước tính",
                    "AVG",
                ),
                ".1%",
            ),
        ),
        (
            datasets["country"],
            titles[7],
            (),
            "echarts_timeseries_bar",
            {
                **horizontal_bar_params(
                    datasets["country"],
                    "country_code",
                    simple_metric("revenue", "Doanh thu"),
                ),
                "adhoc_filters": [complete_filter],
            },
        ),
        (
            datasets["eda"],
            titles[8],
            ("So sánh mô hình |",),
            "echarts_timeseries_bar",
            time_chart_params(
                datasets["eda"],
                "echarts_timeseries_bar",
                simple_metric("revenue_yoy_growth_pct", "Tăng trưởng YoY", "AVG"),
                ".1%",
            ),
        ),
        (
            datasets["eda"],
            titles[9],
            ("Thực tế và dự báo |",),
            "heatmap_v2",
            {
                "datasource": f"{datasets['eda']}__table",
                "viz_type": "heatmap_v2",
                "x_axis": "month_name",
                "groupby": ["year"],
                "metric": simple_metric("revenue", "Doanh thu", "AVG"),
                "adhoc_filters": [
                    sql_filter("is_complete_month = TRUE", "tv3_heatmap_complete_months")
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
    ]

    charts: list[tuple[int, str]] = []
    for dataset_id, slice_name, legacy_prefixes, viz_type, params in chart_specs:
        chart_id = get_or_create_chart(
            client,
            dashboard_id,
            dataset_id,
            slice_name,
            legacy_prefixes,
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
    print(f"Dashboard ready: {BASE_URL}/superset/dashboard/{DASHBOARD_SLUG}/")


if __name__ == "__main__":
    main()
