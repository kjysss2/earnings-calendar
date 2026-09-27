# 26.3Q 실적발표 캘린더 (GitHub Pages)

`data/calendar.json`에 등록된 2026년 3분기 실적발표 일정을 주간 그리드로 보여주는 정적 캘린더입니다. 참고 사이트와 같은 `장전 / 장후 / 시간미정` 구조를 사용하며, 회사 공식 IR 또는 공식 발표자료에서 날짜를 확인한 종목에 `✓ 확정` 배지를 표시합니다.

## 배포

1. GitHub 저장소에서 **Settings → Pages**로 이동합니다.
2. **Branch: main / (root)**를 선택합니다.
3. `https://<아이디>.github.io/earnings-calendar/`에서 확인합니다.

## 일정 데이터

일정은 `data/calendar.json`에서 관리합니다.

```json
{
  "date": "2026-10-08",
  "session": "before",
  "name": "펩시코",
  "ticker": "PEP",
  "confirmed": true,
  "source": "https://공식-IR-출처"
}
```

- `confirmed: true`: 회사 공식 IR·공식 보도자료에서 날짜 확인
- `session: before`: 장 시작 전 발표
- `session: after`: 장 마감 후 발표
- `session: tba`: 발표 세션 미확인
- `focus: true`: 반도체·장비 관련 관심주(파란 점)

현재 데이터는 2026-09-28 KST 기준으로 공식 일정이 확인된 종목만 담았습니다. 회사가 날짜를 발표하지 않은 종목은 예상일을 임의로 넣지 않고, 공식 일정이 확인되면 `calendar.json`에 추가합니다.

## 참고

- 모든 `IR` 링크는 각 회사의 공식 투자자 페이지 또는 공식 발표자료로 연결됩니다.
- 사이트는 별도 빌드 과정 없이 GitHub Pages에서 `index.html`을 바로 제공합니다.
