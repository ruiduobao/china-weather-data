# China Weather Data

Query and download China meteorological station data. Supports data.cma.cn
(authenticated) and Open-Meteo (free fallback).

## Install

### ClawHub
```bash
clawhub install china-weather-data
```

### Manual
```bash
git clone https://github.com/ruiduobao/china-weather-data.git
cd china-weather-data
pip install requests tqdm
```

### Claude Code / skills.sh
```bash
claude skills install china-weather-data
```

## Quick Start

```bash
# Query by city (uses Open-Meteo)
python scripts/china-weather-data.py query --city Beijing --start 2020-01-01 --end 2020-01-31

# Download to CSV
python scripts/china-weather-data.py download --city Shanghai --start 2020-06-01 --end 2020-08-31 --output shanghai.csv

# List stations
python scripts/china-weather-data.py list-stations --province Guangdong
```

## Data Sources

- **Primary**: [中国气象数据网](http://data.cma.cn/) — Official China meteorological data
- **Fallback**: [Open-Meteo](https://open-meteo.com/) — Free, no key required

---

# 中国气象数据查询

查询和下载中国气象站数据。支持 data.cma.cn（需认证）和 Open-Meteo（免费备源）。

## 安装

### ClawHub
```bash
clawhub install china-weather-data
```

### 手动安装
```bash
git clone https://github.com/ruiduobao/china-weather-data.git
cd china-weather-data
pip install requests tqdm
```

### Claude Code / skills.sh
```bash
claude skills install china-weather-data
```

## 快速开始

```bash
# 按城市查询（使用 Open-Meteo）
python scripts/china-weather-data.py query --city Beijing --start 2020-01-01 --end 2020-01-31

# 下载到 CSV
python scripts/china-weather-data.py download --city Shanghai --start 2020-06-01 --end 2020-08-31 --output shanghai.csv

# 列出站点
python scripts/china-weather-data.py list-stations --province Guangdong
```

## 数据来源

- **主源**: [中国气象数据网](http://data.cma.cn/) — 中国官方气象数据
- **备源**: [Open-Meteo](https://open-meteo.com/) — 免费，无需密钥
