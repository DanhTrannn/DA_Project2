select
    purchaseorderid as purchase_order_id,
    revisionnumber as revision_number,
    status as order_status,
    employeeid as employee_id,
    vendorid as vendor_id,
    shipmethodid as ship_method_id,
    orderdate::date as order_date,
    shipdate::date as ship_date,
    subtotal,
    taxamt as tax_amount,
    freight,
    subtotal + taxamt + freight as total_due,
    shipdate::date - orderdate::date as fulfillment_days,
    modifieddate as modified_at
from {{ source('oltp_purchasing', 'purchaseorderheader') }}
