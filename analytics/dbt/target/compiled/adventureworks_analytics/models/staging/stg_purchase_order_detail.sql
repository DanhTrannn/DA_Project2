select
    purchaseorderdetailid as purchase_order_detail_id,
    purchaseorderid as purchase_order_id,
    duedate::date as due_date,
    orderqty as order_quantity,
    productid as product_id,
    unitprice as unit_price,
    orderqty * unitprice as line_total,
    receivedqty as received_quantity,
    rejectedqty as rejected_quantity,
    receivedqty - rejectedqty as stocked_quantity,
    modifieddate as modified_at
from "Adventureworks"."purchasing"."purchaseorderdetail"