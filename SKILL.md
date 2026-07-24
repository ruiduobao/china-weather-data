---
description: 'Query China meteorological station data from data.cma.cn (authenticated)
  or

  Open-Meteo (free fallback). Supports temperature, precipitation, wind, pressure,

  humidity, and sunshine data. Outputs CSV or JSON.

  '
name: china-weather-data
---

# China Weather Data

Query and download China meteorological station data. Supports two data sources:

1. **中国气象数据网** (data.cma.cn) — Official source, requires free registration
2. **Open-Meteo** (open-meteo.com) — Free global fallback, no key required

## Features

- Query by city name, station ID, or lat/lon coordinates
- Download temperature, precipitation, wind, pressure, humidity, sunshine
- List meteorological stations by province
- Automatic fallback to Open-Meteo if data.cma.cn is unavailable
- CSV and JSON output

## Usage

```bash
# Query by city (uses Open-Meteo)
python scripts\china-weather-data.py query --city Beijing --start 2020-01-01 --end 2020-01-31

# Query by coordinates
python scripts\china-weather-data.py query --lat 39.9042 --lon 116.4074 --start 2020-01-01 --end 2020-12-31 --type temperature

# Download to CSV
python scripts\china-weather-data.py download --city Shanghai --start 2020-06-01 --end 2020-08-31 --output shanghai_summer.csv

# List stations
python scripts\china-weather-data.py list-stations --province Guangdong

# Configure API key for data.cma.cn
python scripts\china-weather-data.py configure --key YOUR_API_KEY
```

## Installation

```bash
pip install requests>=2.28.0 tqdm
# Or: pip install -r scripts/requirements.txt
```

## Parameters

### `query` / `download`
| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--city` | No* | — | City name (e.g., "Beijing") |
| `--station` | No* | — | Station ID (data.cma.cn) |
| `--lat` | No* | — | Latitude (for Open-Meteo) |
| `--lon` | No* | — | Longitude (for Open-Meteo) |
| `--start` | Yes | — | Start date (YYYY-MM-DD) |
| `--end` | Yes | — | End date (YYYY-MM-DD) |
| `--type` | No | all | Data type: temperature, precipitation, wind, pressure, humidity, sunshine |
| `--json` | No | false | Output as JSON |
| `--output` | download only | — | Output file path |

### `list-stations`
| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--province` | No | — | Filter by province name |
| `--json` | No | false | Output as JSON |

### `configure`
| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--key` | Yes | — | API key for data.cma.cn |

## Data Sources

- **Primary**: [中国气象数据网](http://data.cma.cn/) — Official China meteorological data
- **Fallback**: [Open-Meteo](https://open-meteo.com/) — Free, no key required
- **License**: Varies by source

### Obtaining data.cma.cn API Key

1. Register at [data.cma.cn](http://data.cma.cn/) (free, requires Chinese phone number)
2. Log in → User Center → API Management
3. Apply for API access (usually approved within 1-2 business days)
4. Copy the API key and run: `python scripts\china-weather-data.py configure --key YOUR_KEY`

### Temporal Resolution

| Source | Resolution | Description |
|--------|------------|-------------|
| data.cma.cn | Hourly, Daily, Monthly | Station observations |
| Open-Meteo | Hourly, Daily | Gridded reanalysis/forecast |

### Units

| Data Type | Unit |
|-----------|------|
| Temperature | °C (摄氏度) |
| Precipitation | mm (毫米) |
| Wind speed | m/s (米/秒) |
| Pressure | hPa (百帕) |
| Humidity | % (相对湿度) |
| Sunshine | hours (小时) |

### Temporal Coverage

- **data.cma.cn**: Varies by station (most from 1951-present)
- **Open-Meteo**: 1940-present (ERA5 reanalysis), forecast up to 16 days

### Automatic Fallback Triggers

The tool automatically falls back to Open-Meteo when:
- No data.cma.cn API key is configured
- data.cma.cn returns HTTP 403/404/500
- data.cma.cn request times out (>30s)
- Requested station ID is not found in data.cma.cn

### City Name Matching

- Supports fuzzy matching (e.g., "Beijing" matches "北京")
- Pinyin input accepted (e.g., "beijing" → "北京")
- Chinese characters preferred for accuracy
- County-level cities supported

### Example Output

```csv
date,temperature,precipitation,wind_speed,pressure,humidity
2020-01-01,2.3,0.0,3.1,1013.2,45
2020-01-02,3.1,0.5,2.8,1012.8,52
2020-01-03,1.8,0.0,4.2,1014.1,40
```

### Citation

**data.cma.cn**:
```bibtex
@misc{chinameteorological,
  title = {China Meteorological Data Service},
  author = {{China Meteorological Administration}},
  howpublished = {\url{http://data.cma.cn/}},
  note = {Accessed: YYYY-MM-DD}
}
```

**Open-Meteo**:
```bibtex
@misc{openmeteo2022,
  title = {Open-Meteo API},
  author = {{Open-Meteo}},
  year = {2022},
  howpublished = {\url{https://open-meteo.com/}},
  note = {Accessed: YYYY-MM-DD}
}
```

## Visualization

- Time series plots: `plt.plot(dates, temperature)` for temperature trends
- Multi-variable subplots: Use `matplotlib` subplots for comparing variables
- Heatmaps: Calendar heatmaps with `calmap` for seasonal patterns
- Wind roses: Use `windrose` package for wind direction/speed

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `ConnectionError` | Network issue | Check internet, retry |
| `HTTP 429` | Rate limit | Wait 60s, retry |
| `ValueError` | Invalid input | Check parameter format |
| Empty output | No data | Try different parameters |
| `ModuleNotFoundError` | Missing dep | Run pip install |
| `HTTP 403` | No API key | Configure key or use Open-Meteo fallback |
| City not found | Name mismatch | Try pinyin or Chinese characters |
| Timeout | Slow API | Increase timeout or use fallback |

---

## Advanced Usage

### Batch City Query
```bash
# Query multiple cities from a list
for city in "北京" "上海" "广州" "成都"; do
  python scripts\china-weather-data.py download     --city "$city" --type temperature     --start 2023-01-01 --end 2023-12-31     --output weather_${city}_2023.csv
  sleep 1
done
```

### CI/CD Integration (GitHub Actions)
```yaml
# .github/workflows/update-weather.yml
name: Update Weather Data
on:
  schedule:
    - cron: '0 7 * * *'  # Daily at 07:00 Beijing time
jobs:
  download:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install requests
      - env:
          CMA_API_KEY: ${{ secrets.CMA_API_KEY }}
        run: |
          python scripts\china-weather-data.py download \
            --city 北京 --type temperature \
            --start $(date -d '7 days ago' +%Y-%m-%d) \
            --end $(date +%Y-%m-%d) \
            --output data/beijing_temp.csv
```

### PostgreSQL/PostGIS Import
```bash
python scripts\china-weather-data.py download   --city 北京 --type temperature   --start 2023-01-01 --end 2023-12-31   --output weather.csv

psql -d gis_db -c "\COPY weather(city, date, temperature) FROM 'weather.csv' CSV HEADER"
```

### Performance Tips
- Open-Meteo fallback is free but less accurate than CMA stations
- Add `sleep 1` between city queries to respect rate limits
- Use `--force-openmeteo` when CMA API is unavailable

---

## 中文说明

查询和下载中国气象站数据。支持两个数据源：

1. **中国气象数据网** (data.cma.cn) — 官方数据源，需免费注册
2. **Open-Meteo** (open-meteo.com) — 免费全球 fallback，无需密钥

### 功能

- 按城市名、站点 ID 或经纬度查询
- 下载温度、降水、风、气压、湿度、日照数据
- 按省份列出气象站
- data.cma.cn 不可用时自动回退到 Open-Meteo
- CSV 和 JSON 输出

### 使用方法

```bash
# 按城市查询（使用 Open-Meteo）
python scripts\china-weather-data.py query --city Beijing --start 2020-01-01 --end 2020-01-31

# 按坐标查询
python scripts\china-weather-data.py query --lat 39.9042 --lon 116.4074 --start 2020-01-01 --end 2020-12-31 --type temperature

# 下载到 CSV
python scripts\china-weather-data.py download --city Shanghai --start 2020-06-01 --end 2020-08-31 --output shanghai_summer.csv

# 列出站点
python scripts\china-weather-data.py list-stations --province Guangdong

# 配置 data.cma.cn API 密钥
python scripts\china-weather-data.py configure --key YOUR_API_KEY
```

### 数据来源

- **主源**: [中国气象数据网](http://data.cma.cn/) — 中国官方气象数据
- **备源**: [Open-Meteo](https://open-meteo.com/) — 免费，无需密钥
- **许可证**: 因数据源而异

### 获取 data.cma.cn API 密钥

1. 在 [data.cma.cn](http://data.cma.cn/) 注册（免费，需要中国手机号）
2. 登录 → 用户中心 → API 管理
3. 申请 API 访问权限（通常 1-2 个工作日批准）
4. 复制 API 密钥并运行: `python scripts\china-weather-data.py configure --key YOUR_KEY`

### 时间分辨率

| 数据源 | 分辨率 | 说明 |
|--------|--------|------|
| data.cma.cn | 逐时、逐日、逐月 | 站点观测 |
| Open-Meteo | 逐时、逐日 | 格点再分析/预报 |

### 单位

| 数据类型 | 单位 |
|----------|------|
| 温度 | °C（摄氏度） |
| 降水 | mm（毫米） |
| 风速 | m/s（米/秒） |
| 气压 | hPa（百帕） |
| 湿度 | %（相对湿度） |
| 日照 | hours（小时） |

### 时间覆盖范围

- **data.cma.cn**: 因站点而异（大多数从 1951 年至今）
- **Open-Meteo**: 1940 年至今（ERA5 再分析），预报最长 16 天

### 自动回退触发条件

以下情况自动回退到 Open-Meteo:
- 未配置 data.cma.cn API 密钥
- data.cma.cn 返回 HTTP 403/404/500
- data.cma.cn 请求超时（>30秒）
- 在 data.cma.cn 中找不到请求的站点 ID

### 城市名称匹配

- 支持模糊匹配（如 "Beijing" 匹配 "北京"）
- 接受拼音输入（如 "beijing" → "北京"）
- 建议使用中文字符以获得最佳精度
- 支持县级市

### 输出示例

```csv
date,temperature,precipitation,wind_speed,pressure,humidity
2020-01-01,2.3,0.0,3.1,1013.2,45
2020-01-02,3.1,0.5,2.8,1012.8,52
2020-01-03,1.8,0.0,4.2,1014.1,40
```

### 引用格式

**data.cma.cn**:
```bibtex
@misc{chinameteorological,
  title = {China Meteorological Data Service},
  author = {{China Meteorological Administration}},
  howpublished = {\url{http://data.cma.cn/}},
  note = {Accessed: YYYY-MM-DD}
}
```

**Open-Meteo**:
```bibtex
@misc{openmeteo2022,
  title = {Open-Meteo API},
  author = {{Open-Meteo}},
  year = {2022},
  howpublished = {\url{https://open-meteo.com/}},
  note = {Accessed: YYYY-MM-DD}
}
```

### 可视化

- 时间序列图: `plt.plot(dates, temperature)` 绘制温度趋势
- 多变量子图: 使用 `matplotlib` subplots 比较不同变量
- 热力图: 使用 `calmap` 创建日历热力图显示季节模式
- 风玫瑰图: 使用 `windrose` 包绘制风向/风速

### 故障排除

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `ConnectionError` | 网络问题 | 检查网络，重试 |
| `HTTP 429` | 速率限制 | 等待 60 秒后重试 |
| `ValueError` | 无效输入 | 检查参数格式 |
| 空输出 | 无数据 | 尝试不同参数 |
| `ModuleNotFoundError` | 缺少依赖 | 运行 pip install |
| `HTTP 403` | 无 API 密钥 | 配置密钥或使用 Open-Meteo 回退 |
| 城市未找到 | 名称不匹配 | 尝试拼音或中文字符 |
| 超时 | API 响应慢 | 增加超时时间或使用回退 |
