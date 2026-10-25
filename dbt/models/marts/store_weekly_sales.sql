select
    store_id,
    week_date,
    weekly_sales,
    is_holiday_week,
    temperature,
    fuel_price,
    cpi,
    unemployment
from {{ ref('stg_walmart_sales') }}
