-- One row per city and hour. Re-ingestions are deduplicated keeping the latest load,
-- so a backfill or a retried run never double counts.
with source as (

    select * from {{ source('weather_raw', 'hourly_observations') }}

),

ranked as (

    select
        city,
        latitude,
        longitude,
        cast(observed_at as timestamp)             as observed_at,
        cast(temperature_c as float64)             as temperature_c,
        cast(relative_humidity_pct as float64)     as relative_humidity_pct,
        cast(coalesce(precipitation_mm, 0) as float64) as precipitation_mm,
        cast(wind_speed_kmh as float64)            as wind_speed_kmh,
        cast(ingested_at as timestamp)             as ingested_at,
        row_number() over (
            partition by city, observed_at
            order by ingested_at desc
        ) as rn
    from source

)

select * except (rn)
from ranked
where rn = 1
