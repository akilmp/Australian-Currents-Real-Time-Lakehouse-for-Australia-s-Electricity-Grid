{{ config(
    materialized='incremental',
    partition_by={'field': 'trading_date'},
    unique_key=['trading_date', 'dispatch_interval', 'unit_id']
) }}

select
    trading_date,
    dispatch_interval,
    unit_id,
    generated_mw
from raw_fact_dispatch
{% if is_incremental() %}
  where trading_date >= (select coalesce(max(trading_date), '1900-01-01') from {{ this }})
{% endif %}
