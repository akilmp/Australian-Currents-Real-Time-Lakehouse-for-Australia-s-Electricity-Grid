{{ config(materialized='table') }}

select
    unit_id,
    trading_date,
    unit_name,
    region_id
from nem.unit_metadata
