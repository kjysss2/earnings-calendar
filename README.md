# 실적발표 캘린더 (GitHub Pages)

실적발표 일정을 주간 그리드(장전/장후)로 보여주고, Notion의 `26.2Q 미국 DB`에 정리된 Transcript 페이지가 있으면 회사명 옆에 링크를 표시하는 사이트입니다.

## 배포 방법

1. GitHub에서 저장소를 엽니다.
2. 저장소 **Settings → Pages → Branch: main / (root)** 를 선택합니다.
3. 1~2분 후 `https://<아이디>.github.io/earnings-calendar/`로 접속합니다.

## 자동 업데이트 동작

`.github/workflows/update.yml`이 30분마다 실행됩니다(매시 7분과 37분, GitHub Actions 스케줄 기준).

- **IR자료**: 더 이상 표시하거나 수집하지 않습니다.
- **Transcript**: Notion의 `26.2Q 미국 DB`에서 캘린더 종목 티커와 일치하는 페이지를 찾아 `data/notion-transcripts.json`에 저장합니다.
- Notion 자동 연결을 쓰려면 GitHub 저장소의 `Settings → Secrets and variables → Actions`에 `NOTION_TOKEN`을 추가해야 합니다.
- `NOTION_TOKEN`이 없으면 기존 `data/notion-transcripts.json` 링크를 유지하고 종료합니다.

## 수동 편집

일정은 `data/calendar.json`에서 직접 수정할 수 있습니다.

```json
{"date": "2026-07-22", "session": "after", "name": "테슬라", "ticker": "TSLA", "hl": true}
```

Transcript 링크를 수동으로 추가하려면 `data/notion-transcripts.json`의 `links`에 티커와 Notion 페이지 URL을 넣으면 됩니다.

```json
{
  "links": {
    "PEP": "https://app.notion.com/p/3992cff291cc8106b877f61c24792ff5"
  }
}
```

## Notion 연결 준비

1. Notion에서 내부 통합을 만들고 Secret 토큰을 발급합니다.
2. `26.2Q 미국 DB` 데이터베이스를 해당 통합에 공유합니다.
3. GitHub Actions Secret에 `NOTION_TOKEN`을 저장합니다.

## 참고

- 사이트에는 Notion 페이지 링크만 표시합니다.
- Notion DB에 없는 종목은 Transcript 버튼이 나타나지 않습니다.
