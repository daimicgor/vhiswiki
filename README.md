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

## 手術賠償估算用嘅數據

| 檔案 | 內容 | 點樣更新 |
| --- | --- | --- |
| `data/benefits.json` | 437 個靈活計劃版本嘅賠償上限（房租、雜費、手術費、麻醉、手術室、額外醫療、年度上限），由官方計劃文件整理並逐項核對 | 計劃改條款時：喺 Actions 執行「下載計劃文件」，再請 Claude 重新整理 |
| `data/surgery-bills.json` | 13 間私家醫院 30 種常見手術嘅 2025 年歷史賬單統計（醫生費、醫院費、總額中位數及第 90 百分值、住院日數） | 每年醫院公布新數據後，用 `tools/research_orphf.py` 同 `tools/parse_orphf.py` 更新 |

| `data/major-treatments.json` | 癌症、心臟等高額治療嘅參考價（中大醫院定價收費、港安醫院、AIG、保泰、富衛公開資料），每項註明來源 | 定期檢查來源網頁有冇改價，直接改呢個檔案 |

標準計劃一律用法定標準計劃上限計算。
