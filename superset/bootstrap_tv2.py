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


DASHBOARD_TITLE = "Hiệu quả sản phẩm AdventureWorks - Doanh thu và rủi ro lợi nhuận"
DASHBOARD_SLUG = "adventureworks-tv2-product-analytics"
LEGACY_DASHBOARD_TITLES = {
    "AdventureWorks Product Performance - Revenue Concentration & Margin Risk",
    "AdventureWorks TV2 - Product & Cross-sell Analytics",
    "AdventureWorks TV2 - Product & Cross-sell Story",
}


def get_or_create_dashboard(client: SupersetClient) -> int:
    for dashboard in client.list_all("dashboard"):
        if dashboard.get("dashboard_title") in {
            DASHBOARD_TITLE,
            *LEGACY_DASHBOARD_TITLES,
        }:
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


def get_or_create_tv2_chart(
    client: SupersetClient,
    dashboard_id: int,
    dataset_id: int,
    slice_name: str,
    legacy_slice_names: tuple[str, ...],
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
    accepted_names = {slice_name, *legacy_slice_names}
    stable_prefixes = {
        f"{name.split('|', 1)[0].strip()} |"
        for name in (slice_name, *legacy_slice_names)
        if "|" in name
    }
    for chart in client.list_all("chart"):
        chart_name = str(chart.get("slice_name") or "")
        if chart_name in accepted_names or any(
            chart_name.startswith(prefix) for prefix in stable_prefixes
        ):
            chart_id = int(chart["id"])
            client.request("PUT", f"/api/v1/chart/{chart_id}", payload)
            return chart_id
    response = client.request("POST", "/api/v1/chart/", payload)
    return int(response["id"])


def numeric_filter(
    subject: str,
    operator: str,
    comparator: int,
    name: str,
) -> dict[str, object]:
    return {
        "clause": "WHERE",
        "comparator": comparator,
        "expressionType": "SIMPLE",
        "filterOptionName": name,
        "operator": operator,
        "sqlExpression": None,
        "subject": subject,
    }


def sold_product_filter() -> dict[str, object]:
    return numeric_filter(
        "revenue",
        ">",
        0,
        "tv2_revenue_greater_than_zero",
    )


def loss_making_filter() -> dict[str, object]:
    return numeric_filter(
        "estimated_gross_profit",
        "<",
        0,
        "tv2_gross_profit_less_than_zero",
    )


def sql_metric(expression: str, label: str, option_name: str) -> dict[str, object]:
    return {
        "expressionType": "SQL",
        "sqlExpression": expression,
        "label": label,
        "optionName": option_name,
    }


def load_story_metrics() -> dict[str, object]:
    source_uri = os.getenv("SUPERSET_SOURCE_URI")
    if not source_uri:
        raise RuntimeError("SUPERSET_SOURCE_URI is required to build TV2 insight titles")

    query = """
        with sold as (
            select *
            from mart_product.product_sales_summary
            where revenue > 0
        ),
        category as (
            select
                product_category_name,
                sum(revenue) as revenue,
                sum(estimated_gross_profit) / nullif(sum(revenue), 0) as margin
            from sold
            group by product_category_name
        ),
        leader as (
            select product_name, revenue
            from sold
            order by revenue desc
            limit 1
        ),
        quantity_leader as (
            select product_name, quantity_sold
            from sold
            order by quantity_sold desc
            limit 1
        ),
        profit_leader as (
            select product_name, estimated_gross_profit
            from sold
            order by estimated_gross_profit desc
            limit 1
        )
        select
            sum(s.revenue) as revenue,
            sum(s.estimated_gross_profit) as gross_profit,
            sum(s.estimated_gross_profit) / nullif(sum(s.revenue), 0) as margin,
            sum(s.quantity_sold) as units,
            count(*) filter (where s.estimated_gross_profit < 0) as loss_products,
            -sum(s.estimated_gross_profit) filter (
                where s.estimated_gross_profit < 0
            ) as gross_profit_leakage,
            (
                select revenue / nullif((select sum(revenue) from category), 0)
                from category
                where product_category_name = 'Bikes'
            ) as bikes_revenue_share,
            (
                select margin
                from category
                where product_category_name = 'Accessories'
            ) as accessories_margin,
            (
                select revenue / nullif((select sum(revenue) from category), 0)
                from category
                where product_category_name = 'Accessories'
            ) as accessories_revenue_share,
            (select product_name from leader) as leader_name,
            (select revenue from leader) as leader_revenue,
            (select product_name from quantity_leader) as quantity_leader_name,
            (select quantity_sold from quantity_leader) as quantity_leader_units,
            (select product_name from profit_leader) as profit_leader_name,
            (
                select estimated_gross_profit
                from profit_leader
            ) as profit_leader_gross_profit,
            (select min(order_date) from core_dw.fact_sales_order_line) as data_start,
            (select max(order_date) from core_dw.fact_sales_order_line) as data_end
        from sold s
    """
    connection_uri = source_uri.replace("postgresql+psycopg2://", "postgresql://", 1)
    with psycopg2.connect(connection_uri) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()
            columns = [description.name for description in cursor.description]
    if row is None:
        raise RuntimeError("Product mart returned no story metrics")
    return dict(zip(columns, row))


def money_millions(value: object, decimals: int) -> str:
    amount = f"{float(value) / 1_000_000:.{decimals}f}".replace(".", ",")
    return f"{amount} triệu USD"


def percentage(value: object) -> str:
    return f"{float(value) * 100:.1f}".replace(".", ",") + "%"


def story_titles(metrics: dict[str, object]) -> list[str]:
    data_start = metrics["data_start"]
    data_end = metrics["data_end"]
    period = f"{data_start:%m/%Y}-{data_end:%m/%Y}"
    return [
        (
            f"Quy mô | Doanh thu {money_millions(metrics['revenue'], 1)} từ "
            f"{float(metrics['units']) / 1_000:.1f} nghìn sản phẩm ({period})".replace(
                ".", ","
            )
        ),
        (
            "Lợi nhuận | Lợi nhuận gộp ước tính đạt "
            f"{money_millions(metrics['gross_profit'], 2)}"
        ),
        f"Biên lợi nhuận | Toàn danh mục chỉ đạt {percentage(metrics['margin'])}",
        f"Rủi ro | {int(metrics['loss_products'])} sản phẩm đang lỗ",
        (
            "Tập trung doanh thu | Xe đạp (Bikes) đóng góp "
            f"{percentage(metrics['bikes_revenue_share'])} doanh thu"
        ),
        (
            "Cơ hội | Phụ kiện (Accessories) đạt biên "
            f"{percentage(metrics['accessories_margin'])} nhưng chỉ chiếm "
            f"{percentage(metrics['accessories_revenue_share'])} doanh thu"
        ),
        (
            f"Dẫn đầu doanh thu | {metrics['leader_name']} đạt "
            f"{money_millions(metrics['leader_revenue'], 1)}"
        ),
        (
            f"Bán chạy nhất | {metrics['quantity_leader_name']} đạt "
            f"{int(metrics['quantity_leader_units']):,} sản phẩm".replace(",", ".")
        ),
        (
            f"Đóng góp lợi nhuận | {metrics['profit_leader_name']} đạt "
            f"{money_millions(metrics['profit_leader_gross_profit'], 2)}"
        ),
        (
            f"Thất thoát | {int(metrics['loss_products'])} sản phẩm làm giảm "
            f"{money_millions(metrics['gross_profit_leakage'], 2)} "
            "lợi nhuận gộp ước tính"
        ),
        "Quyết định | Ưu tiên sản phẩm có doanh thu và biên lợi nhuận cao",
    ]


def dashboard_layout_tv2(charts: list[tuple[int, str]]) -> str:
    if len(charts) != 11:
        raise ValueError(f"TV2 dashboard requires 11 charts, received {len(charts)}")
    chart_lookup = {slice_name: chart_id for chart_id, slice_name in charts}
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
        [(charts[index][1], 3, 18) for index in range(4)],
        [(charts[index][1], 6, 30) for index in range(4, 6)],
        [(charts[index][1], 4, 34) for index in range(6, 9)],
        [(charts[9][1], 12, 46)],
        [(charts[10][1], 12, 38)],
    ]

    row_index = 1
    for section in sections:
        row_id = f"ROW-{row_index}"
        row_index += 1
        layout[grid_id]["children"].append(row_id)  # type: ignore[index]
        chart_nodes = [f"CHART-{chart_lookup[slice_name]}" for slice_name, _, _ in section]
        layout[row_id] = {
            "id": row_id,
            "type": "ROW",
            "children": chart_nodes,
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
            "parents": [root_id, grid_id],
        }
        for slice_name, width, height in section:
            chart_id = chart_lookup[slice_name]
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


def bar_params(
    dataset_id: int,
    dimension: str,
    metric_column: str,
    metric_label: str,
    row_limit: int,
) -> dict[str, object]:
    return {
        "datasource": f"{dataset_id}__table",
        "viz_type": "echarts_timeseries_bar",
        "x_axis": dimension,
        "metrics": [simple_metric(metric_column, metric_label)],
        "groupby": [],
        "adhoc_filters": [sold_product_filter()],
        "row_limit": row_limit,
        "order_desc": True,
        "x_axis_sort": "value",
        "x_axis_sort_asc": False,
        "orientation": "horizontal",
        "show_value": True,
        "show_legend": False,
        "truncate_metric": True,
        "y_axis_format": "SMART_NUMBER",
        "time_range": "No filter",
    }


def main() -> None:
    client = SupersetClient()
    client.login()
    database_id = get_database_id(client)
    product_dataset_id = get_or_create_dataset(
        client,
        database_id,
        "mart_product",
        "product_sales_summary",
    )
    dashboard_id = get_or_create_dashboard(client)
    titles = story_titles(load_story_metrics())

    chart_specs = [
        (
            product_dataset_id,
            titles[0],
            ("01 - Total Product Revenue", "TV2 - Total Product Revenue", "Scale |"),
            "big_number_total",
            {
                "datasource": f"{product_dataset_id}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric("revenue", "Doanh thu"),
                "adhoc_filters": [sold_product_filter()],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            product_dataset_id,
            titles[1],
            (
                "02 - Total Estimated Gross Profit",
                "TV2 - Total Estimated Gross Profit",
                "Profit |",
            ),
            "big_number_total",
            {
                "datasource": f"{product_dataset_id}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric(
                    "estimated_gross_profit",
                    "Lợi nhuận gộp ước tính",
                ),
                "adhoc_filters": [sold_product_filter()],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            product_dataset_id,
            titles[2],
            ("03 - Units Sold", "TV2 - Units Sold", "Margin |"),
            "big_number_total",
            {
                "datasource": f"{product_dataset_id}__table",
                "viz_type": "big_number_total",
                "metric": sql_metric(
                    "SUM(estimated_gross_profit) / NULLIF(SUM(revenue), 0)",
                    "Biên lợi nhuận gộp ước tính",
                    "metric_weighted_gross_margin",
                ),
                "adhoc_filters": [sold_product_filter()],
                "time_range": "No filter",
                "y_axis_format": ".1%",
            },
        ),
        (
            product_dataset_id,
            titles[3],
            ("04 - Top Cross-sell Rules", "TV2 - Top Cross-sell Rules", "Risk |"),
            "big_number_total",
            {
                "datasource": f"{product_dataset_id}__table",
                "viz_type": "big_number_total",
                "metric": simple_metric(
                    "product_key",
                    "Số sản phẩm đang lỗ",
                    "COUNT",
                ),
                "adhoc_filters": [sold_product_filter(), loss_making_filter()],
                "time_range": "No filter",
                "y_axis_format": "SMART_NUMBER",
            },
        ),
        (
            product_dataset_id,
            titles[4],
            (
                "05 - Category Revenue and Gross Profit",
                "TV2 - Category Revenue and Gross Profit",
                "Concentration |",
            ),
            "echarts_timeseries_bar",
            {
                "datasource": f"{product_dataset_id}__table",
                "viz_type": "echarts_timeseries_bar",
                "x_axis": "product_category_name",
                "metrics": [simple_metric("revenue", "Doanh thu")],
                "groupby": [],
                "adhoc_filters": [sold_product_filter()],
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
            product_dataset_id,
            titles[5],
            (
                "07 - Top Products by Quantity",
                "TV2 - Top Products by Quantity",
                "Opportunity |",
            ),
            "echarts_timeseries_bar",
            {
                "datasource": f"{product_dataset_id}__table",
                "viz_type": "echarts_timeseries_bar",
                "x_axis": "product_category_name",
                "metrics": [
                    sql_metric(
                        "SUM(estimated_gross_profit) / NULLIF(SUM(revenue), 0)",
                        "Biên lợi nhuận gộp ước tính",
                        "metric_category_weighted_margin",
                    )
                ],
                "groupby": [],
                "adhoc_filters": [sold_product_filter()],
                "row_limit": 10,
                "order_desc": True,
                "x_axis_sort": "value",
                "x_axis_sort_asc": False,
                "orientation": "horizontal",
                "show_value": True,
                "show_legend": False,
                "y_axis_format": ".1%",
                "time_range": "No filter",
            },
        ),
        (
            product_dataset_id,
            titles[6],
            (
                "06 - Top Products by Revenue",
                "TV2 - Top Products by Revenue",
                "Leader |",
            ),
            "echarts_timeseries_bar",
            bar_params(
                product_dataset_id,
                "product_name",
                "revenue",
                "Doanh thu",
                10,
            ),
        ),
        (
            product_dataset_id,
            titles[7],
            (),
            "echarts_timeseries_bar",
            bar_params(
                product_dataset_id,
                "product_name",
                "quantity_sold",
                "Số lượng bán",
                10,
            ),
        ),
        (
            product_dataset_id,
            titles[8],
            (),
            "echarts_timeseries_bar",
            bar_params(
                product_dataset_id,
                "product_name",
                "estimated_gross_profit",
                "Lợi nhuận gộp ước tính",
                10,
            ),
        ),
        (
            product_dataset_id,
            titles[9],
            (
                "08 - Top Products by Gross Profit",
                "TV2 - Top Products by Gross Profit",
                "Leakage | Loss-making products erode $1.33M gross profit",
            ),
            "table",
            {
                "datasource": f"{product_dataset_id}__table",
                "viz_type": "table",
                "query_mode": "raw",
                "all_columns": [
                    "product_name",
                    "product_category_name",
                    "revenue",
                    "estimated_gross_profit",
                    "estimated_gross_margin_pct",
                ],
                "adhoc_filters": [sold_product_filter(), loss_making_filter()],
                "order_by_cols": ['["estimated_gross_profit", true]'],
                "row_limit": 10,
                "page_length": 10,
            },
        ),
        (
            product_dataset_id,
            titles[10],
            (
                "09 - Product Profitability Matrix",
                "TV2 - Product Profitability Matrix",
                "Decision |",
            ),
            "bubble_v2",
            {
                "datasource": f"{product_dataset_id}__table",
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
                "adhoc_filters": [sold_product_filter()],
                "row_limit": 100,
                "order_desc": True,
                "max_bubble_size": "50",
                "show_legend": True,
                "x_axis_title": "Doanh thu",
                "y_axis_title": "Biên lợi nhuận gộp ước tính",
                "xAxisFormat": "SMART_NUMBER",
                "yAxisFormat": ".1%",
                "time_range": "No filter",
            },
        ),
    ]

    charts: list[tuple[int, str]] = []
    for dataset_id, slice_name, legacy_slice_names, viz_type, params in chart_specs:
        chart_id = get_or_create_tv2_chart(
            client,
            dashboard_id,
            dataset_id,
            slice_name,
            legacy_slice_names,
            viz_type,
            params,
        )
        charts.append((chart_id, slice_name))

    client.request(
        "PUT",
        f"/api/v1/dashboard/{dashboard_id}",
        {
            "dashboard_title": DASHBOARD_TITLE,
            "slug": DASHBOARD_SLUG,
            "published": True,
            "position_json": dashboard_layout_tv2(charts),
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
