# China Weather Data Skill - Development Doc

## Purpose
Query China meteorological station data and download weather records.
Supports both 中国气象数据网 (authenticated) and Open-Meteo (free fallback).

## Data Sources

### Primary: 中国气象数据网 (http://data.cma.cn/)
- Requires registration and API key
- Official China meteorological station data
- Historical records from 1951 onwards
- API: http://data.cma.cn/docDetail/listDoc.html

### Fallback: Open-Meteo (https://open-meteo.com/)
- Free, no API key required
- Global coverage including China
- Historical archive API: https://archive-api.open-meteo.com/v1/archive
- Forecast API: https://api.open-meteo.com/v1/forecast

## CLI Design
```
china-weather-data query --city Beijing --start 2020-01-01 --end 2020-12-31
china-weather-data query --station 54511 --type temperature
china-weather-data download --city Beijing --start 2020-01-01 --end 2020-12-31 --output weather.csv
china-weather-data list-stations --province Beijing
china-weather-data configure --key YOUR_API_KEY
```

### Subcommands
- `query`: query weather data
  - `--city`: city name
  - `--station`: station ID
  - `--lat`/`--lon`: coordinates (for Open-Meteo)
  - `--start`: start date (YYYY-MM-DD)
  --end`: end date (YYYY-MM-DD)
  - `--type`: data type (temperature, precipitation, wind, pressure, humidity, sunshine)
  - `--json`: output as JSON
- `download`: download to file
  - same as query plus `--output`
- `list-stations`: list meteorological stations
  - `--province`: filter by province
- `configure`: set API key
  - `--key`: API key for data.cma.cn

## Privacy
- API key stored locally in ~/.china-weather/config.json
- Only coordinates/dates sent to APIs
- No personal data transmitted

## Error Handling
- Graceful fallback from data.cma.cn to Open-Meteo
- Validate date ranges
- Handle missing station data
