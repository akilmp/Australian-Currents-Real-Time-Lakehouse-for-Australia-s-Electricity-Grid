{{ config(materialized='table') }}

select
    region_id,
    trading_date,
    region_name
from nem.region_metadata
