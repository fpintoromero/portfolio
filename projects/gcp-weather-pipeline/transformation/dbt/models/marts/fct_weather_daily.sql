-- Daily aggregates per city. Partitioned by day and clustered by city (see dbt_project.yml),
-- so dashboards filtering a date range and a city scan only the partitions they need.
-- insert_overwrite rebuilds only the partitions touched by the current run.
{%- set run_date = var('run_date', run_started_at.strftime('%Y-%m-%d')) -%}
{{ config(partitions=["date('" ~ run_date ~ "')", "date_sub(date('" ~ run_date ~ "'), interval 1 day)"]) }}

select
    date(observed_at)                     as observed_date,
    city,
    any_value(latitude)                   as latitude,
    any_value(longitude)                  as longitude,
    count(*)                              as hours_observed,
    round(min(temperature_c), 1)          as temp_min_c,
    round(max(temperature_c), 1)          as temp_max_c,
    round(avg(temperature_c), 1)          as temp_avg_c,
    round(sum(precipitation_mm), 1)       as precipitation_total_mm,
    round(max(wind_speed_kmh), 1)         as wind_max_kmh,
    max(ingested_at)                      as last_ingested_at
from {{ ref('stg_weather_hourly') }}
{% if is_incremental() %}
where date(observed_at) >= date_sub(date('{{ run_date }}'), interval 1 day)
{% endif %}
group by observed_date, city
