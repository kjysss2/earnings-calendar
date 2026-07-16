#!/usr/bin/env python3
"""
kjysss2/earnings-calendar의 data/calendar.json에
HOOD, NET, RBRK 일정을 추가하거나 갱신하는 스크립트입니다.

사용법:
    earnings-calendar 저장소 최상위 폴더에서 실행

    python patch_rbrk_net_hood.py

수정 파일:
    data/calendar.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CALENDAR_PATH = Path("data/calendar.json")

TARGET_ENTRIES: list[dict[str, Any]] = [
    {
        "date": "2026-07-29",
        "session": "after",
        "name": "로빈후드",
        "ticker": "HOOD",
        "hl": True,
    },
    {
        "date": "2026-08-06",
        "session": "after",
        "name": "클라우드플레어",
        "ticker": "NET",
        "hl": True,
    },
    {
        # 회사 공식 일정이 확정되기 전까지 예상 일정으로 표시
        "date": "2026-09-08",
        "session": "after",
        "name": "루브릭(예상)",
        "ticker": "RBRK",
        "hl": True,
    },
]

SESSION_ORDER = {
    "before": 0,
    "after": 1,
    "tba": 2,
}


def load_calendar(path: Path) -> dict[str, Any]:
    """calendar.json 파일을 불러옵니다."""

    if not path.exists():
        raise FileNotFoundError(
            f"{path} 파일을 찾을 수 없습니다.\n"
            "earnings-calendar 저장소 최상위 폴더에서 실행하세요."
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("calendar.json의 최상위 데이터가 객체가 아닙니다.")

    if not isinstance(data.get("entries"), list):
        raise ValueError("calendar.json에 entries 배열이 없습니다.")

    return data


def upsert_entries(
    entries: list[dict[str, Any]],
    target_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    같은 티커가 이미 존재하면 해당 항목을 갱신하고,
    존재하지 않으면 새 항목으로 추가합니다.
    """

    entries_by_ticker: dict[str, dict[str, Any]] = {}

    for entry in entries:
        ticker = str(entry.get("ticker", "")).upper().strip()

        if ticker:
            entries_by_ticker[ticker] = entry

    for target in target_entries:
        ticker = str(target["ticker"]).upper().strip()

        if ticker in entries_by_ticker:
            entries_by_ticker[ticker].update(target)
            print(f"갱신: {ticker}")
        else:
            new_entry = dict(target)
            entries.append(new_entry)
            entries_by_ticker[ticker] = new_entry
            print(f"추가: {ticker}")

    return entries


def sort_entries(
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """날짜, 장전·장후 구분, 회사명 순서로 정렬합니다."""

    return sorted(
        entries,
        key=lambda entry: (
            str(entry.get("date", "")),
            SESSION_ORDER.get(
                str(entry.get("session", "tba")),
                9,
            ),
            str(entry.get("name", "")),
            str(entry.get("ticker", "")),
        ),
    )


def save_calendar(
    path: Path,
    data: dict[str, Any],
) -> None:
    """수정된 데이터를 calendar.json에 저장합니다."""

    with path.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")


def main() -> None:
    data = load_calendar(CALENDAR_PATH)

    data["entries"] = upsert_entries(
        entries=data["entries"],
        target_entries=TARGET_ENTRIES,
    )

    data["entries"] = sort_entries(data["entries"])
    data["updated"] = "2026-07-16 KST"

    save_calendar(
        path=CALENDAR_PATH,
        data=data,
    )

    print()
    print("수정 완료: data/calendar.json")
    print("- HOOD: 2026-07-29 장후, 빨간색")
    print("- NET: 2026-08-06 장후, 빨간색")
    print("- RBRK: 2026-09-08 장후 예상, 빨간색")


if __name__ == "__main__":
    main()