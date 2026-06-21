select
    md5(country_code || '|' || year::text || '|' || indicator_code) as observation_key,
    upper(country_code) as country_code,
    country_name,
    year,
    indicator_code,
    indicator_name,
    value::numeric as indicator_value,
    unit,
    source_name,
    source_url,
    retrieved_at::date as retrieved_at
from "Adventureworks"."raw_macro"."macro_observations"
where value is not null