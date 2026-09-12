#!/usr/bin/env python3
"""
Fetches hourly SNOTEL data for Tony Grove Lake (station 823, UT) and computes:
  - snowfall totals over the last 24h / 48h / 7 days (change in snow depth)
  - high / low observed air temperature over each of those windows
  - current total snow depth

Writes the result to data.json in the repo root, which index.html reads.
"""

import json
import sys
import urllib.request
from datetime import datetime, timedelta

STATION = "823:ut:SNTL"
CSV_URL = (
    "https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/"
    f"hourly/{STATION}/-167,0/WTEQ::value,SNWD::value,PREC::value,TOBS::value"
)

OUTPUT_PATH = "data.json"


def fetch_csv(url):
    req = urllib.request.Request(url, headers={"User-Agent": "wheretobrap-snow-bot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_float(s):
    s = s.strip()
    return float(s) if s else None


def parse_rows(csv_text):
    rows = []
    for line in csv_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("Date,"):
            continue
        parts = line.split(",")
        if len(parts) < 5:
            continue
        try:
            dt = datetime.strptime(parts[0], "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        rows.append(
            {
                "dt": dt,
                "wteq": parse_float(parts[1]),
                "snwd": parse_float(parts[2]),
                "prec": parse_float(parts[3]),
                "tobs": parse_float(parts[4]),
            }
        )
    rows.sort(key=lambda r: r["dt"])
    return rows


def latest_value(rows, field):
    for r in reversed(rows):
        if r[field] is not None:
            return r[field], r["dt"]
    return None, None


def value_at_or_before(rows, target_dt, field):
    best = None
    for r in rows:
        if r["dt"] <= target_dt and r[field] is not None:
            best = r
        if r["dt"] > target_dt:
            break
    return best[field] if best else None


def high_low(rows, start_dt, end_dt, field):
    vals = [r[field] for r in rows if r[field] is not None and start_dt <= r["dt"] <= end_dt]
    if not vals:
        return None, None
    return max(vals), min(vals)


def round_or_none(x, n=1):
    return None if x is None else round(x, n)


def main():
    try:
        csv_text = fetch_csv(CSV_URL)
        rows = parse_rows(csv_text)
        if not rows:
            raise ValueError("No data rows parsed from SNOTEL response")

        latest_dt = rows[-1]["dt"]
        current_depth, current_depth_dt = latest_value(rows, "snwd")

        periods = {}
        for label, hours in (("last_24h", 24), ("last_48h", 48), ("last_7d", 24 * 7)):
            start_dt = latest_dt - timedelta(hours=hours)
            start_depth = value_at_or_before(rows, start_dt, "snwd")
            snowfall = None
            if start_depth is not None and current_depth is not None:
                snowfall = max(0.0, round(current_depth - start_depth, 1))
            high, low = high_low(rows, start_dt, latest_dt, "tobs")
            periods[label] = {
                "snowfall_in": snowfall,
                "high_f": round_or_none(high),
                "low_f": round_or_none(low),
            }

        data = {
            "station": {
                "name": "Tony Grove Lake",
                "id": 823,
                "state": "UT",
                "elevation_ft": 8450,
            },
            "as_of": latest_dt.strftime("%Y-%m-%d %H:%M"),
            "current_snow_depth_in": round_or_none(current_depth),
            "current_snow_depth_as_of": current_depth_dt.strftime("%Y-%m-%d %H:%M")
            if current_depth_dt
            else None,
            "periods": periods,
            "fetched_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "ok",
        }

    except Exception as e:
        # Never crash the workflow silently — write an error status the page can show.
        data = {
            "status": "error",
            "error": str(e),
            "fetched_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        print(f"ERROR fetching/parsing SNOTEL data: {e}", file=sys.stderr)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
