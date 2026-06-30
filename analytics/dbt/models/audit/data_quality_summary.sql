with checks as (
    select
        'fact_sales_order_line'::text as model_name,
        'null_sales_order_id'::text as check_name,
        count(*) filter (where sales_order_id is null) as failed_record_count
    from {{ ref('fact_sales_order_line') }}

    union all

    select
        'fact_sales_order_line',
        'null_customer_key',
        count(*) filter (where customer_key is null)
    from {{ ref('fact_sales_order_line') }}

    union all

    select
        'fact_sales_order_line',
        'null_product_key',
        count(*) filter (where product_key is null)
    from {{ ref('fact_sales_order_line') }}

    union all

    select
        'fact_sales_order_line',
        'negative_quantity',
        count(*) filter (where order_quantity < 0)
    from {{ ref('fact_sales_order_line') }}

    union all

    select
        'fact_sales_order_line',
        'negative_net_sales',
        count(*) filter (where net_sales < 0)
    from {{ ref('fact_sales_order_line') }}

    union all

    select
        'fact_sales_order_line',
        'duplicate_sales_order_detail_id',
        count(*) - count(distinct sales_order_detail_id)
    from {{ ref('fact_sales_order_line') }}

    union all

    select
        'fact_sales_order',
        'duplicate_sales_order_id',
        count(*) - count(distinct sales_order_id)
    from {{ ref('fact_sales_order') }}

    union all

    select
        'fact_sales_order',
        'invalid_order_date',
        count(*) filter (where order_date is null or due_date < order_date)
    from {{ ref('fact_sales_order') }}

    union all

    select
        'fact_sales_order_line',
        'negative_unit_price',
        count(*) filter (where unit_price < 0)
    from {{ ref('fact_sales_order_line') }}

    union all

    select
        'fact_sales_order_line',
        'invalid_discount_rate',
        count(*) filter (where unit_price_discount < 0 or unit_price_discount > 1)
    from {{ ref('fact_sales_order_line') }}

    union all

    select
        'business_kpi_macro_period',
        'missing_macro_context',
        count(*) filter (where macro_coverage_status = 'missing_macro_data')
    from {{ ref('business_kpi_macro_period') }}
)

select
    model_name,
    check_name,
    failed_record_count,
    case
        when check_name = 'missing_macro_context' and failed_record_count > 0 then 'WARN'
        when failed_record_count = 0 then 'PASS'
        else 'FAIL'
    end as status,
    current_timestamp as checked_at
from checks
