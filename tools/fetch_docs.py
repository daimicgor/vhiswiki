"""下載所有在售計劃嘅計劃文件 (英文版 PDF) 並轉成文字，供整理保障上限用。"""
import json, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs-text"
OUT.mkdir(exist_ok=True)
BASE = "https://www.vhis.gov.hk"


def active(x):
    return not (x.get("de-reg") or x.get("unavailable") or x.get("renewal-only"))


urls = {}
for fn in ["standard-plans.json", "flexi-plans.json"]:
    for p in json.loads((ROOT / "data/raw" / fn).read_text("utf-8"))["certified-plans"]:
        if not active(p):
            continue
        for v in p["plan-info-certified"]:
            if active(v):
                urls[v["certification-no"]] = BASE + v["plan-doc-url"]["en"]

ok = fail = 0
for cert, url in sorted(urls.items()):
    txt = OUT / f"{cert}.txt"
    if txt.exists() and txt.stat().st_size > 1000:
        ok += 1
        continue
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (vhiswiki docs fetcher)"})
            pdf = urllib.request.urlopen(req, timeout=90).read()
            tmp = Path("/tmp/doc.pdf")
            tmp.write_bytes(pdf)
            subprocess.run(["pdftotext", "-layout", str(tmp), str(txt)], check=True)
            ok += 1
            break
        except Exception as e:
            if attempt == 2:
                fail += 1
                print(f"失敗 {cert}: {e}")
            time.sleep(3)
    time.sleep(0.3)
(OUT / "index.json").write_text(json.dumps(urls, indent=1), "utf-8")
print(f"完成：{ok} 份成功，{fail} 份失敗，共 {len(urls)} 份")
