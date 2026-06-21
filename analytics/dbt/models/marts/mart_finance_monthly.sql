-- OLTP does not contain a complete general ledger. Keep an explicit empty
-- contract until the group approves an external finance source.
select
    null::date as month,
    null::text as account_type,
    null::text as account_description,
    null::numeric as amount
where false
