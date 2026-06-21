select
    productcategoryid as product_category_id,
    name as product_category_name,
    rowguid,
    modifieddate as modified_at
from {{ source('oltp_production', 'productcategory') }}
