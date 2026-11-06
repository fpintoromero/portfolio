-- Singular test: a day can never have a minimum above its maximum.
select *
from {{ ref('fct_weather_daily') }}
where temp_min_c > temp_max_c
