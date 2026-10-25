with source as (
    select * from {{ source('walmart', 'raw_walmart_sales') }}
),

renamed as (
    select
        cast(store as int) as store_id,
        coalesce(
            to_date(sale_date, 'M/d/yyyy'),
            to_date(sale_date, 'yyyy-MM-dd')
        ) as week_date,
        cast(weekly_sales as double) as weekly_sales,
        cast(holiday_flag as boolean) as is_holiday_week,
        cast(temperature as double) as temperature,
        cast(fuel_price as double) as fuel_price,
        cast(cpi as double) as cpi,
        cast(unemployment as double) as unemployment
    from source
)

select * from renamed
