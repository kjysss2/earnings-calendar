#!/usr/bin/env python3
"""
Notion의 '26.2Q 미국 DB'를 조회해
data/notion-transcripts.json을 자동 갱신합니다.

Transcript 검색 대상은 아래 두 파일의 티커를 합쳐 사용합니다.

- data/calendar.json
- data/semiconductor-additions.json

Notion 페이지 제목 예시:

AAL - American Airlines Group Inc. Q2 2026
KMI - Kinder Morgan Inc. Q2 2026
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
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    ROOT,
    "data",
)

CALENDAR_FILES = [
    os.path.join(
        DATA_DIR,
        "calendar.json",
    ),
    os.path.join(
        DATA_DIR,
        "semiconductor-additions.json",
    ),
]

OUTPUT_FILE = os.path.join(
    DATA_DIR,
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


def notion_request(
    method,
    endpoint,
    payload=None,
):
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
            "Authorization": (
                f"Bearer {NOTION_TOKEN}"
            ),
            "Notion-Version": (
                NOTION_VERSION
            ),
            "Content-Type": (
                "application/json"
            ),
        },
    )

    try:
        with urlopen(
            request,
            timeout=30,
        ) as response:
            response_text = (
                response.read().decode(
                    "utf-8"
                )
            )

            return json.loads(
                response_text
            )

    except HTTPError as exc:
        detail = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        raise RuntimeError(
            f"Notion API 오류: "
            f"HTTP {exc.code}\n"
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


def ticker_from_title(
    title,
    valid_tickers,
):
    """
    예:
    AAL - American Airlines Group Inc. Q2 2026

    위 제목에서 AAL을 추출합니다.
    """

    title_upper = title.upper()

    match = re.match(
        r"^\s*"
        r"([A-Z][A-Z0-9.\-]{0,9})"
        r"\s*[-–—]\s*",
        title_upper,
    )

    if not match:
        return None

    ticker = match.group(1)

    if ticker in valid_tickers:
        return ticker

    return None


def collect_valid_tickers():
    """
    calendar.json과
    semiconductor-additions.json의
    티커를 합칩니다.
    """

    valid_tickers = set()

    for path in CALENDAR_FILES:
        data = read_json(
            path,
            {
                "entries": [],
            },
        )

        entries = data.get(
            "entries",
            [],
        )

        if not isinstance(
            entries,
            list,
        ):
            raise RuntimeError(
                f"entries가 배열이 아닙니다: "
                f"{path}"
            )

        file_tickers = set()

        for item in entries:
            if not isinstance(
                item,
                dict,
            ):
                continue

            ticker = str(
                item.get(
                    "ticker",
                    "",
                )
            ).upper().strip()

            if not ticker:
                continue

            file_tickers.add(
                ticker
            )

            valid_tickers.add(
                ticker
            )

        print(
            f"{os.path.basename(path)}: "
            f"티커 {len(file_tickers)}개 확인"
        )

    if not valid_tickers:
        raise RuntimeError(
            "일정 데이터에서 "
            "티커를 찾지 못했습니다."
        )

    print(
        f"Transcript 검색 대상: "
        f"총 {len(valid_tickers)}개"
    )

    return valid_tickers


def get_data_source_ids():
    database_id = re.sub(
        r"[^0-9a-fA-F]",
        "",
        NOTION_DATABASE_ID,
    )

    if len(database_id) != 32:
        raise RuntimeError(
            "NOTION_DATABASE_ID가 "
            "올바르지 않습니다."
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
        source_id = source.get(
            "id"
        )

        if source_id:
            data_source_ids.append(
                source_id
            )

    if not data_source_ids:
        raise RuntimeError(
            "Notion 데이터베이스의 "
            "data source를 찾지 못했습니다. "
            "26.2Q 미국 DB를 "
            "Notion Integration에 "
            "연결했는지 확인하세요."
        )

    return data_source_ids


def query_pages(
    data_source_id,
):
    pages = []
    cursor = None

    while True:
        payload = {
            "page_size": 100,
        }

        if cursor:
            payload[
                "start_cursor"
            ] = cursor

        response = notion_request(
            "POST",
            (
                f"/data_sources/"
                f"{data_source_id}/query"
            ),
            payload,
        )

        results = response.get(
            "results",
            [],
        )

        pages.extend(
            results
        )

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


def collect_transcript_links(
    valid_tickers,
):
    matched = {}
    total_pages = 0

    data_source_ids = (
        get_data_source_ids()
    )

    for data_source_id in (
        data_source_ids
    ):
        pages = query_pages(
            data_source_id
        )

        total_pages += len(
            pages
        )

        for page in pages:
            title = page_title(
                page
            )

            ticker = ticker_from_title(
                title,
                valid_tickers,
            )

            url = page.get(
                "url"
            )

            edited = page.get(
                "last_edited_time",
                "",
            )

            if not ticker:
                continue

            if not url:
                continue

            old = matched.get(
                ticker
            )

            # 같은 티커 페이지가 여러 개라면
            # 가장 최근에 수정된 페이지를 사용합니다.
            if (
                old is None
                or edited > old["edited"]
            ):
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
        links[ticker] = item[
            "url"
        ]

    return links


def main():
    if not NOTION_TOKEN:
        raise RuntimeError(
            "GitHub Actions Secret에 "
            "NOTION_TOKEN이 없습니다."
        )

    # calendar.json과
    # semiconductor-additions.json을
    # 모두 읽습니다.
    valid_tickers = (
        collect_valid_tickers()
    )

    links = (
        collect_transcript_links(
            valid_tickers
        )
    )

    previous = read_json(
        OUTPUT_FILE,
        {
            "source": (
                "Notion 26.2Q 미국 DB"
            ),
            "databaseId": (
                NOTION_DATABASE_ID
            ),
            "links": {},
        },
    )

    previous_links = previous.get(
        "links",
        {},
    )

    if links == previous_links:
        print(
            "변경된 Transcript 링크가 "
            "없습니다."
        )

        return

    kst = timezone(
        timedelta(
            hours=9
        )
    )

    output = {
        "source": (
            "Notion 26.2Q 미국 DB"
        ),
        "databaseId": (
            NOTION_DATABASE_ID
        ),
        "updated": datetime.now(
            kst
        ).strftime(
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
