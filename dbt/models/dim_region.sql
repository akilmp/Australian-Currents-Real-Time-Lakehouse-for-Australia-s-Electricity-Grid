{{ config(
    materialized='incremental',
    partition_by={'field': 'trading_date'},
    unique_key='region_id'
) }}

select
    region_id,
    trading_date,
    region_name
from {{ ref('raw_dim_region') }}
{% if is_incremental() %}
  where trading_date >= (select coalesce(max(trading_date), '1900-01-01') from {{ this }})
{% endif %}
