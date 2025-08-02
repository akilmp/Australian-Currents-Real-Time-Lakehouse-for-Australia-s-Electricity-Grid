{{ config(materialized='table') }}

select
    trading_interval,
    unit_id,
    generated_mw,
    fuel_type,
    trading_date
from nem.silver_dispatch_clean
