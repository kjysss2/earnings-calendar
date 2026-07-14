#!/usr/bin/env python3
"""Update data/calendar.json from StockEasy market-calendar earnings data."""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(ROOT, "data", "calendar.json")
API_URL = "https://stockeasy.intellio.kr/stockdata/api/v1/market-calendar"
KST = timezone(timedelta(hours=9))
MONTH_WINDOW = int(os.environ.get("STOCKEASY_MONTH_WINDOW", "6"))


def add_months(base, offset):
    month_index = base.month - 1 + offset
    year = base.year + month_index // 12
    month = month_index % 12 + 1
    return year, month


def fetch_month(year, month):
    query = urlencode({"year": year, "month": month, "category": "earnings"})
    request = Request(
        f"{API_URL}?{query}",
        headers={
            "Accept": "application/json",
            "User-Agent": "earnings-calendar/1.0 (+https://kjysss2.github.io/earnings-calendar/)",
        },
    )

    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"StockEasy API error: HTTP {exc.code}\n{detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"StockEasy API connection failed: {exc}") from exc
    except TimeoutError as exc:
        raise RuntimeError("StockEasy API request timed out.") from exc


def normalize_item(item):
    date = str(item.get("record_date") or "").strip()
    company = str(item.get("company") or "").strip()
    symbol = str(item.get("symbol") or "").strip()

    if not date or not company:
        return None

    entry = {
        "date": date,
        "session": "tba",
        "name": company,
        "ticker": symbol,
        "market": str(item.get("market") or "").strip(),
        "eventType": str(item.get("event_type") or "").strip(),
    }

    detail = str(item.get("detail") or "").strip()
    if detail:
        entry["detail"] = detail

    return entry


def build_calendar():
    current_month = datetime.now(KST).date().replace(day=1)
    entries = []
    seen = set()

    for offset in range(MONTH_WINDOW):
        year, month = add_months(current_month, offset)
        payload = fetch_month(year, month)

        for item in payload.get("items", []):
            entry = normalize_item(item)
            if entry is None:
                continue

            key = (
                entry["date"],
                entry.get("ticker", ""),
                entry.get("name", ""),
                entry.get("eventType", ""),
            )

            if key in seen:
                continue

            seen.add(key)
            entries.append(entry)

    entries.sort(key=lambda item: (item["date"], item.get("name", ""), item.get("ticker", "")))

    updated = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    fallback_date = datetime.now(KST).strftime("%Y-%m-%d")

    return {
        "title": "\uAD6D\uB0B4 \uC2E4\uC801\uBC1C\uD45C \uC77C\uC815 (StockEasy)",
        "source": "StockEasy \uC2DC\uC7A5\uC77C\uC815 \uC2E4\uC801\uBC1C\uD45C",
        "updated": updated,
        "startDate": entries[0]["date"] if entries else fallback_date,
        "endDate": entries[-1]["date"] if entries else fallback_date,
        "entries": entries,
    }


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def main():
    calendar = build_calendar()
    write_json(OUTPUT_FILE, calendar)
    print(f"Updated {OUTPUT_FILE}")
    print(f"Entries: {len(calendar['entries'])}")
    print(f"Range: {calendar['startDate']} ~ {calendar['endDate']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
