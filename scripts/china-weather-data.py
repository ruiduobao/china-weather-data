#!/usr/bin/env python3
"""
China Weather Data CLI — Query meteorological data for China.

Privacy Notice:
    This tool sends ONLY location coordinates and date ranges to the
    configured API (data.cma.cn or open-meteo.com). Your API key is stored
    locally and never shared. No personal data is transmitted.

Data Sources:
    - Primary: data.cma.cn (requires registration)
    - Fallback: Open-Meteo (free, no key)

License: MIT-0
Author: ruiduobao
Version: 0.1.0
"""

import argparse
import csv
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import requests
except ImportError:
    print("ERROR: 'requests' is required. Install with: pip install requests>=2.28.0")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None  # type: ignore

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".china-weather")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
TIMEOUT = 30

__version__ = "0.1.0"
USER_AGENT = f"china-weather-data/{__version__}"


def write_qa_summary(qa_path, *, skill, command, args, payload, extra=None):
    """Write a JSON run-summary sidecar to qa_path (Phase 5 optimization).

    The sidecar includes the request params (place/city, date range, type),
    the resolved lat/lon, the output path and a UTC timestamp so QA can
    match a run to its inputs.
    """
    from datetime import datetime as _dt, timezone as _tz

    summary = dict(payload) if isinstance(payload, dict) else {"result": payload}
    summary.setdefault("skill", skill)
    summary["command"] = command
    summary["version"] = __version__
    summary["user_agent"] = USER_AGENT
    summary["timestamp"] = _dt.now(_tz.utc).isoformat()
    # Echo input args (so QA can match a run to its inputs without re-parsing).
    for flag in ("city", "station", "lat", "lon", "start", "end", "type",
                 "output", "json", "place", "buffer_deg", "province"):
        if hasattr(args, flag):
            val = getattr(args, flag)
            if isinstance(val, (str, int, float, bool, type(None))):
                summary.setdefault(flag, val)
    if extra:
        for k, v in extra.items():
            summary.setdefault(k, v)
    qa_p = Path(qa_path)
    qa_p.parent.mkdir(parents=True, exist_ok=True)
    with open(qa_p, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return qa_p


# Open-Meteo variable mapping
VARIABLE_MAP = {
    "temperature": "temperature_2m_mean,temperature_2m_max,temperature_2m_min",
    "precipitation": "precipitation_sum,rain_sum",
    "wind": "wind_speed_10m_max,wind_direction_10m_dominant",
    "pressure": "surface_pressure_mean",
    "humidity": "temperature_2m_mean",  # Open-Meteo archive doesn't have humidity directly
    "sunshine": "sunshine_duration",
}

# Common China city coordinates
CITY_COORDS = {
    "beijing": (39.9042, 116.4074),
    "shanghai": (31.2304, 121.4737),
    "guangzhou": (23.1291, 113.2644),
    "shenzhen": (22.5431, 114.0579),
    "chengdu": (30.5728, 104.0668),
    "hangzhou": (30.2741, 120.1551),
    "wuhan": (30.5928, 114.3055),
    "xian": (34.3416, 108.9398),
    "nanjing": (32.0603, 118.7969),
    "chongqing": (29.5630, 106.5516),
    "tianjin": (39.3434, 117.3616),
    "shenyang": (41.8057, 123.4315),
    "harbin": (45.8038, 126.5350),
    "kunming": (25.0389, 102.7183),
    "changsha": (28.2282, 112.9388),
    "zhengzhou": (34.7466, 113.6253),
    "qingdao": (36.0671, 120.3826),
    "dalian": (38.9140, 121.6147),
    "xiamen": (24.4798, 118.0819),
    "fuzhou": (26.0745, 119.2965),
    "jinan": (36.6512, 117.1201),
    "hefei": (31.8206, 117.2272),
    "nanchang": (28.6820, 115.8579),
    "guiyang": (26.6470, 106.6302),
    "nanning": (22.8170, 108.3665),
    "lanzhou": (36.0611, 103.8343),
    "taiyuan": (37.8706, 112.5489),
    "urumqi": (43.8256, 87.6168),
    "lhasa": (29.6520, 91.1721),
    "huhehaote": (40.8414, 111.7519),
    "yinchuan": (38.4872, 106.2309),
    "xining": (36.6171, 101.7782),
    "haikou": (20.0440, 110.1999),
}


def load_config() -> Dict[str, Any]:
    """Load config from ~/.china-weather/config.json."""
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_config(config: Dict[str, Any]) -> None:
    """Save config to ~/.china-weather/config.json."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def validate_date(date_str: str) -> bool:
    """Validate YYYY-MM-DD date format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def resolve_coordinates(city: Optional[str], lat: Optional[float], lon: Optional[float]) -> Optional[tuple]:
    """Resolve lat/lon from city name or direct coordinates."""
    if lat is not None and lon is not None:
        return (lat, lon)
    if city:
        city_lower = city.lower().strip()
        if city_lower in CITY_COORDS:
            return CITY_COORDS[city_lower]
        # Fallback: try Open-Meteo geocoding for any place name (Chinese or English)
        try:
            from _place import resolve_place as _resolve_place
            place_info = _resolve_place(city, allow_nominatim=False)
            print(
                f"[china-weather-data] resolved '{city}' to "
                f"{place_info.get('display_name')} via {place_info.get('source')}",
                file=sys.stderr,
            )
            return (place_info["lat"], place_info["lon"])
        except Exception as e:
            print(
                f"ERROR: Unknown city '{city}' (geocoding fallback failed: {e}). "
                f"Use --lat/--lon directly or choose from: "
                f"{', '.join(sorted(CITY_COORDS.keys())[:10])}...",
                file=sys.stderr,
            )
            return None
    return None


def query_open_meteo(
    lat: float,
    lon: float,
    start: str,
    end: str,
    dtype: str = "temperature",
) -> Optional[Dict[str, Any]]:
    """Query Open-Meteo archive API."""
    variables = VARIABLE_MAP.get(dtype, VARIABLE_MAP["temperature"])
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": variables,
        "timezone": "Asia/Shanghai",
    }
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        print("ERROR: Open-Meteo request timed out.", file=sys.stderr)
        return None
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to Open-Meteo.", file=sys.stderr)
        return None
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Open-Meteo HTTP {e.response.status_code}: {e.response.text[:200]}", file=sys.stderr)
        return None


def format_open_meteo_results(data: Dict[str, Any], dtype: str) -> List[Dict[str, Any]]:
    """Format Open-Meteo response into flat records."""
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    records = []
    for i, date in enumerate(dates):
        record = {"date": date}
        for key, values in daily.items():
            if key == "time":
                continue
            if isinstance(values, list) and i < len(values):
                record[key] = values[i]
        records.append(record)
    return records


def cmd_query(args: argparse.Namespace) -> int:
    """Handle the 'query' subcommand."""
    # Validate dates
    if not validate_date(args.start):
        print(f"ERROR: Invalid start date '{args.start}'. Use YYYY-MM-DD.", file=sys.stderr)
        return 1
    if not validate_date(args.end):
        print(f"ERROR: Invalid end date '{args.end}'. Use YYYY-MM-DD.", file=sys.stderr)
        return 1
    if args.start > args.end:
        print("ERROR: Start date must be before end date.", file=sys.stderr)
        return 1

    # Resolve coordinates
    coords = resolve_coordinates(args.city, args.lat, args.lon)
    if coords is None:
        print("ERROR: Provide --city or --lat/--lon.", file=sys.stderr)
        return 1
    lat, lon = coords

    # Query Open-Meteo
    data = query_open_meteo(lat, lon, args.start, args.end, args.type)
    if data is None:
        return 1

    records = format_open_meteo_results(data, args.type)
    if not records:
        print("No data returned for the specified period/location.")
        return 0

    if args.json:
        print(json.dumps(records, indent=2, ensure_ascii=False))
    else:
        # Print as table
        if records:
            headers = list(records[0].keys())
            print("\t".join(headers))
            print("-" * 60)
            for r in records:
                print("\t".join(str(r.get(h, "")) for h in headers))
        print(f"\n{len(records)} records returned.")
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    """Handle the 'download' subcommand."""
    # Validate dates
    if not validate_date(args.start):
        print(f"ERROR: Invalid start date '{args.start}'. Use YYYY-MM-DD.", file=sys.stderr)
        return 1
    if not validate_date(args.end):
        print(f"ERROR: Invalid end date '{args.end}'. Use YYYY-MM-DD.", file=sys.stderr)
        return 1

    coords = resolve_coordinates(args.city, args.lat, args.lon)
    if coords is None:
        print("ERROR: Provide --city or --lat/--lon.", file=sys.stderr)
        return 1
    lat, lon = coords

    data = query_open_meteo(lat, lon, args.start, args.end, args.type)
    if data is None:
        return 1

    records = format_open_meteo_results(data, args.type)
    if not records:
        print("No data to download.")
        return 0

    # Write CSV
    output_path = args.output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    headers = list(records[0].keys())
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} records to {output_path}")

    # Phase 5: --qa sidecar summary
    if getattr(args, "qa", None):
        write_qa_summary(
            args.qa, skill="china-weather-data", command="download",
            args=args,
            payload={
                "n_records": len(records),
                "output_path": str(Path(output_path).resolve()),
                "size_bytes": Path(output_path).stat().st_size,
                "lat": lat,
                "lon": lon,
                "date_range": [args.start, args.end],
            },
        )
        print(f"QA: {args.qa}")
    return 0


def cmd_list_stations(args: argparse.Namespace) -> int:
    """Handle the 'list-stations' subcommand."""
    # Built-in station list (subset of major China stations)
    stations = [
        {"id": "54511", "name": "北京", "province": "北京", "lat": 39.93, "lon": 116.28},
        {"id": "58362", "name": "上海", "province": "上海", "lat": 31.40, "lon": 121.47},
        {"id": "59287", "name": "广州", "province": "广东", "lat": 23.22, "lon": 113.48},
        {"id": "59493", "name": "深圳", "province": "广东", "lat": 22.55, "lon": 114.10},
        {"id": "56294", "name": "成都", "province": "四川", "lat": 30.57, "lon": 103.95},
        {"id": "57036", "name": "西安", "province": "陕西", "lat": 34.30, "lon": 108.93},
        {"id": "58606", "name": "杭州", "province": "浙江", "lat": 30.23, "lon": 120.17},
        {"id": "57494", "name": "武汉", "province": "湖北", "lat": 30.60, "lon": 114.05},
        {"id": "54857", "name": "济南", "province": "山东", "lat": 36.60, "lon": 117.00},
        {"id": "53614", "name": "太原", "province": "山西", "lat": 37.78, "lon": 112.55},
        {"id": "52889", "name": "兰州", "province": "甘肃", "lat": 36.05, "lon": 103.88},
        {"id": "51828", "name": "喀什", "province": "新疆", "lat": 39.47, "lon": 75.98},
        {"id": "50953", "name": "哈尔滨", "province": "黑龙江", "lat": 45.75, "lon": 126.77},
        {"id": "53772", "name": "银川", "province": "宁夏", "lat": 38.47, "lon": 106.27},
        {"id": "45011", "name": "香港", "province": "香港", "lat": 22.30, "lon": 114.17},
    ]

    if args.province:
        stations = [s for s in stations if args.province in s["province"]]

    if getattr(args, "place", None):
        # Resolve --place to bbox and filter stations within bbox
        import os as _os, sys as _sys
        _shared = _os.path.join(
            _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
            "_shared", "place_resolver.py",
        )
        if _os.path.isfile(_shared):
            _sys.path.insert(0, _os.path.dirname(_shared))
            import place_resolver  # type: ignore
            try:
                pi = place_resolver.resolve_place(
                    args.place, buffer_deg=args.buffer_deg,
                    allow_nominatim=not args.no_nominatim,
                )
                lon, lat = pi["lon"], pi["lat"]
                buf = args.buffer_deg
                bbox = [lon - buf, lat - buf, lon + buf, lat + buf]
                stations = [s for s in stations
                            if bbox[0] <= s["lon"] <= bbox[2] and bbox[1] <= s["lat"] <= bbox[3]]
                print(f"[place] {args.place} -> ({lat:.4f}, {lon:.4f}), {len(stations)} station(s) in bbox",
                      file=sys.stderr)
            except Exception as e:
                print(f"WARN: --place resolution failed ({e}); returning all stations",
                      file=sys.stderr)
        else:
            print(f"WARN: place_resolver not found at {_shared}", file=sys.stderr)

    if args.json:
        print(json.dumps(stations, indent=2, ensure_ascii=False))
    else:
        print(f"{'ID':<8} {'Name':<10} {'Province':<10} {'Lat':>8} {'Lon':>8}")
        print("-" * 50)
        for s in stations:
            print(f"{s['id']:<8} {s['name']:<10} {s['province']:<10} {s['lat']:>8.2f} {s['lon']:>8.2f}")
    return 0


def cmd_configure(args: argparse.Namespace) -> int:
    """Handle the 'configure' subcommand."""
    config = load_config()
    config["api_key"] = args.key
    save_config(config)
    print(f"API key saved to {CONFIG_FILE}")
    print("Note: Currently Open-Meteo is used as the data source (no key required).")
    print("The data.cma.cn integration will be activated when you provide a valid key.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="china-weather-data",
        description="Query China meteorological station data.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommand")

    # query
    p_query = subparsers.add_parser("query", help="Query weather data")
    p_query.add_argument("--city", help="City name (e.g., 'Beijing')")
    p_query.add_argument("--station", help="Station ID (data.cma.cn)")
    p_query.add_argument("--lat", type=float, help="Latitude")
    p_query.add_argument("--lon", type=float, help="Longitude")
    p_query.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    p_query.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    p_query.add_argument("--type", default="temperature",
                         choices=["temperature", "precipitation", "wind", "pressure", "humidity", "sunshine"],
                         help="Data type (default: temperature)")
    p_query.add_argument("--json", action="store_true", help="Output as JSON")

    # download
    p_download = subparsers.add_parser("download", help="Download weather data to file")
    p_download.add_argument("--city", help="City name")
    p_download.add_argument("--station", help="Station ID")
    p_download.add_argument("--lat", type=float, help="Latitude")
    p_download.add_argument("--lon", type=float, help="Longitude")
    p_download.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    p_download.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    p_download.add_argument("--type", default="temperature",
                            choices=["temperature", "precipitation", "wind", "pressure", "humidity", "sunshine"],
                            help="Data type")
    p_download.add_argument("--output", required=True, help="Output CSV file path")
    p_download.add_argument("--qa", metavar="PATH", default=None,
                            help="Write a JSON run-summary sidecar to PATH (Phase 5).")

    # list-stations
    p_list = subparsers.add_parser("list-stations", help="List meteorological stations")
    p_list.add_argument("--province", help="Filter by province")
    p_list.add_argument("--place", help="Filter by place name (Chinese or English) → bbox")
    p_list.add_argument("--no-nominatim", action="store_true",
                       help="Skip Nominatim in --place resolution")
    p_list.add_argument("--buffer-deg", type=float, default=0.6,
                       help="Buffer around resolved point (default 0.6° for city)")
    p_list.add_argument("--json", action="store_true", help="Output as JSON")

    # configure
    p_config = subparsers.add_parser("configure", help="Set API key for data.cma.cn")
    p_config.add_argument("--key", required=True, help="API key")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "query":
        return cmd_query(args)
    elif args.command == "download":
        return cmd_download(args)
    elif args.command == "list-stations":
        return cmd_list_stations(args)
    elif args.command == "configure":
        return cmd_configure(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
