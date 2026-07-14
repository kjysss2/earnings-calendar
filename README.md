# Earnings Calendar (GitHub Pages)

This site shows only the StockEasy market-calendar earnings announcement category in the same weekly calendar layout used by the existing page.

## Data Update

.github/workflows/update.yml runs every 3 hours and writes data/calendar.json from:

https://stockeasy.intellio.kr/stockdata/api/v1/market-calendar?category=earnings

The browser only reads the local JSON file, which avoids cross-origin browser fetch issues.

## Manual Data Shape

{"date":"2026-07-14","session":"tba","name":"Samsung Electronics","ticker":"005930","market":"KOSPI"}

session may be before, after, or tba. StockEasy earnings events currently do not include a release time, so the updater writes tba and the page labels that row as earnings announcements.

## Note

Data source: StockEasy market calendar. This page is for schedule reference only.
