#!/usr/bin/env python3
"""
Notion의 '26.2Q 미국 DB'를 확인해
data/notion-transcripts.json을 자동으로 갱신합니다.

Notion 페이지 제목 형식:
TICKER - Company Name Q2 2026

예:
DAL - Delta Air Lines Q2 2026
PEP - PepsiCo Q2 2026
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

CALENDAR_FILE = os.path.join(
    ROOT,
    "data",
    "calendar.json",
)

OUTPUT_FILE = os.path.join(
    ROOT,
    "data",
    "notion-transcripts.json",
)


NOTION_TOKEN = os.environ.get(
    "NOTION_TOKEN",
    "",
).strip()


NOTION_DATABASE_ID = os.environ.get(
    "NOTION_DATABASE_ID",
    "d2c2cff2-91cc-82ac-ac28-0153506c607c",
).strip()


NOTION_VERSION = "2026-03-11"
NOTION_API = "https://api.notion.com/v1"


def read_json(path, fallback):
    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except FileNotFoundError:
        return fallback

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"JSON 형식 오류: {path}\n{exc}"
        ) from exc


def write_json(path, data):
    os.makedirs(
        os.path.dirname(path),
        exist_ok=True,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

        file.write("\n")


def notion_request(method, endpoint, payload=None):
    url = f"{NOTION_API}{endpoint}"

    if payload is None:
        body = None
    else:
        body = json.dumps(
            payload
        ).encode("utf-8")

    request = Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )

    try:
        with urlopen(
            request,
            timeout=30,
        ) as response:
            response_text = response.read().decode(
                "utf-8"
            )

            return json.loads(response_text)

    except HTTPError as exc:
        detail = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Notion API 오류: HTTP {exc.code}\n"
            f"요청 주소: {url}\n"
            f"응답 내용: {detail}"
        ) from exc

    except URLError as exc:
        raise RuntimeError(
            f"Notion 연결 실패: {exc}"
        ) from exc

    except TimeoutError as exc:
        raise RuntimeError(
            "Notion 요청 시간이 초과됐습니다."
        ) from exc


def page_title(page):
    properties = page.get(
        "properties",
        {},
    )

    for prop in properties.values():
        if prop.get("type") != "title":
            continue

        title_parts = prop.get(
            "title",
            [],
        )

        return "".join(
            item.get(
                "plain_text",
                "",
            )
            for item in title_parts
        ).strip()

    return ""


def ticker_from_title(title, valid_tickers):
    """
    DAL - Delta Air Lines Q2 2026
    위 제목에서 DAL을 추출합니다.
    """

    title_upper = title.upper()

    match = re.match(
        r"^\s*([A-Z][A-Z0-9.\-]{0,9})"
        r"\s*[-–—]\s*",
        title_upper,
    )

    if not match:
        return None

    ticker = match.group(1)

    if ticker in valid_tickers:
        return ticker

    return None


def get_data_source_ids():
    database_id = re.sub(
        r"[^0-9a-fA-F]",
        "",
        NOTION_DATABASE_ID,
    )

    if len(database_id) != 32:
        raise RuntimeError(
            "NOTION_DATABASE_ID가 올바르지 않습니다."
        )

    database = notion_request(
        "GET",
        f"/databases/{database_id}",
    )

    data_sources = database.get(
        "data_sources",
        [],
    )

    data_source_ids = []

    for source in data_sources:
        source_id = source.get("id")

        if source_id:
            data_source_ids.append(
                source_id
            )

    if not data_source_ids:
        raise RuntimeError(
            "Notion 데이터베이스의 data source를 "
            "찾지 못했습니다. "
            "26.2Q 미국 DB를 Notion Integration에 "
            "연결했는지 확인하세요."
        )

    return data_source_ids


def query_pages(data_source_id):
    pages = []
    cursor = None

    while True:
        payload = {
            "page_size": 100,
        }

        if cursor:
            payload["start_cursor"] = cursor

        response = notion_request(
            "POST",
            f"/data_sources/{data_source_id}/query",
            payload,
        )

        results = response.get(
            "results",
            [],
        )

        pages.extend(results)

        has_more = response.get(
            "has_more",
            False,
        )

        if not has_more:
            break

        cursor = response.get(
            "next_cursor"
        )

        if not cursor:
            break

        time.sleep(0.2)

    return pages


def collect_transcript_links(valid_tickers):
    matched = {}
    total_pages = 0

    data_source_ids = get_data_source_ids()

    for data_source_id in data_source_ids:
        pages = query_pages(
            data_source_id
        )

        total_pages += len(pages)

        for page in pages:
            title = page_title(page)

            ticker = ticker_from_title(
                title,
                valid_tickers,
            )

            url = page.get("url")

            edited = page.get(
                "last_edited_time",
                "",
            )

            if not ticker:
                continue

            if not url:
                continue

            old = matched.get(ticker)

            # 같은 티커 페이지가 여러 개면
            # 최근 수정된 페이지를 사용합니다.
            if old is None:
                matched[ticker] = {
                    "url": url,
                    "edited": edited,
                    "title": title,
                }

            elif edited > old["edited"]:
                matched[ticker] = {
                    "url": url,
                    "edited": edited,
                    "title": title,
                }

    print(
        f"Notion에서 확인한 페이지: "
        f"{total_pages}개"
    )

    print(
        f"Transcript가 연결된 종목: "
        f"{len(matched)}개"
    )

    for ticker, item in sorted(
        matched.items()
    ):
        print(
            f"- {ticker}: "
            f"{item['title']}"
        )

    links = {}

    for ticker, item in sorted(
        matched.items()
    ):
        links[ticker] = item["url"]

    return links


def main():
    if not NOTION_TOKEN:
        raise RuntimeError(
            "GitHub Actions Secret에 "
            "NOTION_TOKEN이 없습니다."
        )

    calendar = read_json(
        CALENDAR_FILE,
        {
            "entries": [],
        },
    )

    valid_tickers = set()

    for item in calendar.get(
        "entries",
        [],
    ):
        ticker = item.get("ticker")

        if ticker:
            valid_tickers.add(
                str(ticker)
                .upper()
                .strip()
            )

    if not valid_tickers:
        raise RuntimeError(
            "data/calendar.json에서 "
            "티커를 찾지 못했습니다."
        )

    previous = read_json(
        OUTPUT_FILE,
        {
            "source": "Notion 26.2Q 미국 DB",
            "databaseId": NOTION_DATABASE_ID,
            "links": {},
        },
    )

    links = collect_transcript_links(
        valid_tickers
    )

    previous_links = previous.get(
        "links",
        {},
    )

    # 링크가 바뀌었을 때만 파일을 수정합니다.
    if links == previous_links:
        print(
            "변경된 Transcript 링크가 없습니다."
        )

        return

    kst = timezone(
        timedelta(hours=9)
    )

    output = {
        "source": "Notion 26.2Q 미국 DB",
        "databaseId": NOTION_DATABASE_ID,
        "updated": datetime.now(kst).strftime(
            "%Y-%m-%d %H:%M KST"
        ),
        "links": links,
    }

    write_json(
        OUTPUT_FILE,
        output,
    )

    print(
        "data/notion-transcripts.json "
        "업데이트 완료"
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print(
            f"실행 실패: {exc}",
            file=sys.stderr,
        )

        sys.exit(1)
