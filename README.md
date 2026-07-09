# 실적발표 캘린더 (GitHub Pages)

실적발표 일정을 주간 그리드(장전/장후)로 보여주고, 발표 후 IR자료·어닝콜 스크립트가 올라오면 회사명 옆에 버튼이 자동으로 생기는 사이트입니다.

## 배포 방법 (5분)

1. GitHub에서 새 저장소 생성 (예: `earnings-calendar`, Public)
2. 이 폴더의 파일 전체를 업로드 (`.github` 폴더 포함 — 드래그&드롭 시 숨김폴더 누락 주의, `git push` 권장)
3. 저장소 **Settings → Pages → Branch: main / (root)** 선택 → 저장
4. 1~2분 후 `https://<아이디>.github.io/earnings-calendar/` 접속

## 자동 업데이트 동작

`.github/workflows/update.yml`이 3시간마다 실행됩니다.

- **IR자료 버튼**: SEC EDGAR에서 실적발표일 이후 제출된 8-K/6-K 공시(실적 보도자료 포함)를 찾아 자동 연결. API 키 불필요.
- **스크립트 버튼**: FMP(financialmodelingprep.com) API 키가 있으면 어닝콜 스크립트를 받아 `transcripts/` 폴더에 저장 후 연결.
  - 저장소 **Settings → Secrets and variables → Actions → New repository secret**에 이름 `FMP_API_KEY`로 등록
  - 키가 없으면 스크립트 버튼만 생략되고 나머지는 정상 동작
- 첫 실행은 **Actions 탭 → 실적자료 자동 업데이트 → Run workflow**로 수동 실행 가능

## 수동 편집

`data/calendar.json`에서 직접 수정할 수 있습니다. 자동 업데이트는 비어있는(null) 항목만 채우므로 수동으로 넣은 링크는 덮어쓰지 않습니다.

```json
{"date": "2026-07-22", "session": "after", "name": "테슬라", "ticker": "TSLA",
 "hl": true, "ir": "https://...", "script": "https://..."}
```

- `session`: `"before"`(장전) / `"after"`(장후)
- `hl`: `true`면 빨간색 강조
- 다음 달 일정은 `month`를 바꾸고 `entries`를 교체하면 됩니다

## 참고

- 스크립트 저장본은 개인 참고용으로만 사용하세요.
- 샌드빅(SDVKY) 등 SEC 미등록 해외종목은 자동 감지가 안 될 수 있어 수동 링크 등록이 필요합니다.
