#!/usr/bin/env python3
"""
실적발표 캘린더 자동 업데이트 스크립트
- IR자료: SEC EDGAR에서 실적발표일 이후 제출된 8-K/6-K 공시를 찾아 링크 연결 (API 키 불필요)
- 스크립트: FMP_API_KEY 환경변수가 있으면 어닝콜 스크립트를 받아 transcripts/ 폴더에 저장 후 링크 연결
- 이미 값이 채워진 항목(수동 입력 포함)은 절대 덮어쓰지 않음
"""
import json, os, re, sys, time, html
from datetime import date, datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(ROOT, "data", "calendar.json")
TDIR = os.path.join(ROOT, "transcripts")
UA = {"User-Agent": "earnings-calendar personal site kjysss2@gmail.com"}
FMP_KEY = os.environ.get("FMP_API_KEY", "").strip()

def get_json(url, headers=UA, retries=2):
    for i in range(retries + 1):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as e:
            if i == retries:
                print(f"  ! 요청 실패: {url} ({e})")
                return None
            time.sleep(2)

def load_cik_map():
    data = get_json("https://www.sec.gov/files/company_tickers.json")
    if not data:
        return {}
    return {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in data.values()}

def find_edgar_filing(cik, event_date):
    """실적발표일-1 ~ +7일 사이 제출된 8-K/6-K에서 보도자료(EX-99) 직링크 반환"""
    sub = get_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
    if not sub:
        return None
    r = sub.get("filings", {}).get("recent", {})
    forms, dates, accs, prims = r.get("form", []), r.get("filingDate", []), r.get("accessionNumber", []), r.get("primaryDocument", [])
    lo = (event_date - timedelta(days=1)).isoformat()
    hi = (event_date + timedelta(days=7)).isoformat()
    for form, fdate, acc, prim in zip(forms, dates, accs, prims):
        if form in ("8-K", "6-K") and lo <= fdate <= hi:
            base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-','')}"
            # 첨부 문서 중 실적 보도자료(ex-99*.htm)를 찾아 직링크
            idx = get_json(f"{base}/index.json")
            if idx:
                for item in idx.get("directory", {}).get("item", []):
                    n = item.get("name", "").lower()
                    if "99" in n and n.endswith((".htm", ".html")):
                        return f"{base}/{item['name']}"
            if prim:
                return f"{base}/{prim}"
            return f"{base}/{acc}-index.htm"
    return None

def find_transcript(ticker, event_date):
    """FMP에서 실적발표일 이후 스크립트가 올라왔으면 저장하고 상대경로 반환"""
    if not FMP_KEY:
        return None
    lst = get_json(f"https://financialmodelingprep.com/api/v4/earning_call_transcript?symbol={ticker}&year={event_date.year}&apikey={FMP_KEY}", headers={})
    if not lst:
        return None
    for q, y, d in lst:  # [quarter, year, "YYYY-MM-DD HH:MM:SS"]
        if str(d)[:10] >= event_date.isoformat():
            tr = get_json(f"https://financialmodelingprep.com/api/v3/earning_call_transcript/{ticker}?quarter={q}&year={y}&apikey={FMP_KEY}", headers={})
            if tr and tr[0].get("content"):
                os.makedirs(TDIR, exist_ok=True)
                fname = f"{ticker}_{y}Q{q}.html"
                body = html.escape(tr[0]["content"]).replace("\n", "<br>\n")
                with open(os.path.join(TDIR, fname), "w", encoding="utf-8") as f:
                    f.write(f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{ticker} {y} Q{q} 어닝콜 스크립트</title>
<style>body{{max-width:860px;margin:30px auto;padding:0 16px;font-family:Georgia,serif;line-height:1.7;color:#222}}
h1{{font-size:20px;border-bottom:2px solid #1a56a8;padding-bottom:8px}}</style></head>
<body><h1>{ticker} — {y} Q{q} Earnings Call ({str(d)[:10]})</h1><p>{body}</p></body></html>""")
                return f"transcripts/{fname}"
    return None

def main():
    with open(CAL, encoding="utf-8") as f:
        cal = json.load(f)

    today = datetime.now(timezone(timedelta(hours=-4))).date()  # 미 동부 기준
    cik_map, changed = None, False

    for e in cal["entries"]:
        ticker = (e.get("ticker") or "").upper()
        if not ticker:
            continue
        edate = date.fromisoformat(e["date"])
        if edate > today:
            continue  # 아직 발표 전

        if not e.get("ir"):
            if cik_map is None:
                cik_map = load_cik_map()
            cik = cik_map.get(ticker)
            if cik:
                url = find_edgar_filing(cik, edate)
                if url:
                    e["ir"] = url
                    changed = True
                    print(f"IR자료 연결: {e['name']} ({ticker})")
                time.sleep(0.15)

        if not e.get("script"):
            # 1순위: FMP 키가 있으면 스크립트 전문 저장
            path = find_transcript(ticker, edate)
            if path:
                e["script"] = path
                changed = True
                print(f"스크립트 연결: {e['name']} ({ticker})")
            # 2순위(키 불필요): 발표 확인(IR자료 존재) 시 무료 열람 검색 링크 연결
            elif e.get("ir"):
                q = (edate.month + 2) // 3
                e["script"] = ("https://www.google.com/search?q=" +
                               f"{ticker}+Q{q}+{edate.year}+earnings+call+transcript")
                changed = True
                print(f"Transcript 검색링크 연결: {e['name']} ({ticker})")

    if changed:
        cal["updated"] = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M KST")
        with open(CAL, "w", encoding="utf-8") as f:
            json.dump(cal, f, ensure_ascii=False, indent=2)
        print("calendar.json 업데이트 완료")
    else:
        print("변경 사항 없음")

if __name__ == "__main__":
    main()
