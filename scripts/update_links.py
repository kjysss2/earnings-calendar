#!/usr/bin/env python3
"""
실적발표 캘린더 Transcript 링크 업데이트 스크립트
- IR자료는 더 이상 수집하거나 표시하지 않습니다.
- Transcript는 Notion의 "26.2Q 미국 DB"에서 찾은 페이지 URL을 data/notion-transcripts.json에 저장합니다.
- NOTION_TOKEN이 없으면 기존 Notion 링크 파일을 유지하고 종료합니다.
"""
import json
import os
import re
import time
from datetime import datetime, timezone, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(ROOT, "data", "calendar.json")
OUT = os.path.join(ROOT, "data", "notion-transcripts.json")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "").strip()
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "d2c2cff2-91cc-82ac-ac28-0153506c607c").strip()
NOTION_VERSION = "2022-06-28"


def read_json(path, fallback):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return fallback


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def notion_request(url, payload):
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        },
        method="POST",
    )
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def title_from_page(page):
    for prop in page.get("properties", {}).values():
        if prop.get("type") == "title":
            return "".join(part.get("plain_text", "") for part in prop.get("title", [])).strip()
    return ""


def ticker_from_title(title, tickers):
    text = title.upper()
    for ticker in sorted(tickers, key=len, reverse=True):
        if re.search(rf"(^|[^A-Z0-9]){re.escape(ticker)}([^A-Z0-9]|$)", text):
            return ticker
    return None


def fetch_notion_links(tickers):
    links = {}
    cursor = None
    while True:
        payload = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        data = notion_request(f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query", payload)
        for page in data.get("results", []):
            title = title_from_page(page)
            ticker = ticker_from_title(title, tickers)
            if ticker:
                links[ticker] = page.get("url")
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
        time.sleep(0.2)
    return links


def main():
    cal = read_json(CAL, {"entries": []})
    tickers = {str(item.get("ticker", "")).upper() for item in cal.get("entries", []) if item.get("ticker")}
    previous = read_json(OUT, {"source": "Notion 26.2Q 미국 DB", "databaseId": NOTION_DATABASE_ID, "links": {}})

    if not NOTION_TOKEN:
        print("NOTION_TOKEN이 없어 기존 Notion Transcript 링크를 유지합니다.")
        if not os.path.exists(OUT):
            write_json(OUT, previous)
        return

    try:
        links = fetch_notion_links(tickers)
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"Notion 조회 실패: {exc}. 기존 링크를 유지합니다.")
        return

    merged = {**previous.get("links", {}), **links}
    output = {
        "source": "Notion 26.2Q 미국 DB",
        "databaseId": NOTION_DATABASE_ID,
        "updated": datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M KST"),
        "links": dict(sorted((k, v) for k, v in merged.items() if v)),
    }
    write_json(OUT, output)
    print(f"Notion Transcript 링크 {len(output['links'])}개 저장")


if __name__ == "__main__":
    main()
