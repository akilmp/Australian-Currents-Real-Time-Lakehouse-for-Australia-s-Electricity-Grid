{{ config(
    materialized='incremental',
    partition_by={'field': 'trading_date'},
    unique_key='unit_id'
) }}

select
    unit_id,
    trading_date,
    unit_name,
    region_id
from {{ ref('raw_dim_unit') }}
{% if is_incremental() %}
  where trading_date >= (select coalesce(max(trading_date), '1900-01-01') from {{ this }})
{% endif %}
