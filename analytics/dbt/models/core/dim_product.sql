select
    p.product_id as product_key,
    p.product_id,
    p.product_number,
    p.product_name,
    p.color,
    p.size,
    p.product_line,
    p.class,
    p.style,
    p.standard_cost,
    p.list_price,
    p.safety_stock_level,
    p.reorder_point,
    p.is_finished_good,
    p.is_manufactured_in_house,
    p.sell_start_date,
    p.sell_end_date,
    sc.product_subcategory_id,
    sc.product_subcategory_name,
    c.product_category_id,
    c.product_category_name
from {{ ref('stg_product') }} p
left join {{ ref('stg_product_subcategory') }} sc
    using (product_subcategory_id)
left join {{ ref('stg_product_category') }} c
    using (product_category_id)

