# vhiswiki 自願醫保百科

香港自願醫保（VHIS）保費比較網站。由 beezy（FWD 持牌保險代理，保監局牌照 JA3466）營運。

## 點樣自動更新

GitHub 每日香港時間早上 9:17 會自動：

1. 由 vhis.gov.hk 下載最新嘅認可計劃名單同標準保費
2. 重新建立網站
3. 發佈到網上

數據有改動時，`data/raw` 會自動多一個「數據更新」紀錄，可以喺 commit 歷史睇返每次改價。

## 想即刻更新

撳上面 **Actions** → **更新並發佈網站** → **Run workflow**。

## 檔案

| 檔案 | 用途 |
| --- | --- |
| `src/template.html` | 網站外觀同功能（改文字、披露資料喺呢度） |
| `build.py` | 下載數據、整理、砌網頁 |
| `data/raw/` | 最近一次成功下載嘅政府數據 |
| `.github/workflows/update.yml` | 每日自動執行嘅設定 |
| `CNAME` | （有自己域名時先加）域名名稱，例如 `vhiswiki.com` |

數據來源：[DATA.GOV.HK](https://data.gov.hk/tc-data/dataset/hk-hhb-hhbvhis-vhis-standard-premium)。
