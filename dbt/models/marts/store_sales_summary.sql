select
    store_id,
    count(*) as weeks_reported,
    sum(weekly_sales) as total_weekly_sales,
    avg(weekly_sales) as average_weekly_sales,
    max(weekly_sales) as highest_weekly_sales,
    sum(case when is_holiday_week then weekly_sales else 0 end) as holiday_week_sales,
    min(week_date) as first_week,
    max(week_date) as last_week
from {{ ref('stg_walmart_sales') }}
group by store_id
