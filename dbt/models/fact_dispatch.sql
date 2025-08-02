{{ config(
    materialized='incremental',
    partition_by={'field': 'trading_interval'},
    unique_key=['trading_interval', 'unit_id']
) }}

select
    trading_interval,
    unit_id,
    generated_mw,
    trading_date,
    fuel_type
from {{ ref('raw_fact_dispatch') }}
{% if is_incremental() %}
  where trading_interval >= (select coalesce(max(trading_interval), '1900-01-01') from {{ this }})
{% endif %}
