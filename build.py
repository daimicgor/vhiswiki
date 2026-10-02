"""vhiswiki 網站建立程式

1. 由 vhis.gov.hk 下載最新政府開放數據（下載失敗就沿用 data/raw 入面上次嘅檔案）
2. 整理成網站用嘅數據
3. 砌成 site/index.html

用法：
    python build.py            # 下載最新數據再建立網站
    python build.py --offline  # 唔下載，只用 data/raw 現有檔案
"""
import collections
import io
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
RAW = ROOT / "data" / "raw"
SITE = ROOT / "site"
BASE = "https://www.vhis.gov.hk"
SOURCES = {
    "standard-plans.json": BASE + "/public/data/standard-plans.json",
    "flexi-plans.json": BASE + "/public/data/flexi-plans.json",
    "plan-premium.json": BASE + "/public/data/plan-premium.zip",
}
SITE_URL = "https://vhiswiki.com"  # 有自己域名之後喺度改


# ---------- 下載 ----------
def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (vhiswiki data updater)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def download():
    ok = True
    for name, url in SOURCES.items():
        try:
            body = fetch(url)
            if url.endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(body)) as z:
                    inner = [n for n in z.namelist() if n.endswith(".json")][0]
                    body = z.read(inner)
            data = json.loads(body)
            if not data.get("certified-plans"):
                raise ValueError("檔案冇 certified-plans 內容")
            (RAW / name).write_bytes(body)
            print(f"已下載 {name}（{len(data['certified-plans'])} 項）")
        except Exception as e:  # 政府網站間中會失敗，沿用舊檔
            ok = False
            print(f"::warning::下載 {name} 失敗，沿用上次數據：{e}")
    return ok


# ---------- 整理 ----------
SHORT = [
    ("友邦", "AIA"), ("保誠", "保誠"), ("宏利", "宏利"), ("富衛", "富衛 FWD"), ("滙豐", "滙豐"),
    ("中銀", "中銀"), ("安盛", "AXA 安盛"), ("永明", "永明"), ("藍十字", "藍十字"), ("保柏", "保柏 Bupa"),
    ("信諾", "信諾 Cigna"), ("萬通", "萬通"), ("富通", "富通"), ("周大福", "周大福人壽"), ("中國人壽", "中國人壽"),
    ("太平", "中國太平"), ("忠意", "忠意"), ("安達", "安達 Chubb"), ("三井住友", "三井住友"), ("利寶", "利寶"),
    ("蘇黎世", "蘇黎世"), ("保泰", "保泰 Bowtie"), ("Bowtie", "保泰 Bowtie"), ("保特", "保特 bolttech"),
    ("立橋", "立橋"), ("富邦", "富邦"), ("愛心", "愛心人壽"), ("亞洲保險", "亞洲保險"), ("AXA", "AXA 安盛"),
    ("Avo", "Avo"), ("Yas", "YAS"), ("東亞", "東亞"), ("紐約人壽", "紐約人壽"), ("大新", "大新"), ("星展", "星展"),
    ("財險", "國壽財險"), ("閩信", "閩信"), ("香港人壽", "香港人壽"), ("安我", "Avo 安我"), ("中國平安", "平安"),
    ("恒生", "恒生"), ("Blue Cross", "藍十字"),
]


def short(name):
    for k, v in SHORT:
        if k in name:
            return v
    n = re.sub(r"（香港）|\(香港\)|（國際）|\(國際\)|有限公司|股份|保險|人壽", "", name)
    return n.strip()[:8] or name


def parse_level(lv):
    ded, dcur = None, None
    m = re.search(r"([\d,]+)\s*(港元|美元)\s*自付費", lv) or re.search(r"自付費\s*([\d,]+)\s*(港元|美元)", lv)
    if m:
        ded = int(m.group(1).replace(",", ""))
        dcur = "USD" if m.group(2) == "美元" else "HKD"
    room = "半私家房" if "半私家" in lv else "私家房" if "私家" in lv else "普通房" if "普通" in lv else None
    region = next((k for k in ["亞洲及澳紐", "全球", "亞洲"] if k in lv), None)
    return ded, dcur, room, region


def active(x):
    return not (x.get("de-reg") or x.get("unavailable") or x.get("renewal-only"))


def build_data():
    prem = {r["certification-no"]: r for r in json.loads((RAW / "plan-premium.json").read_text("utf-8"))["certified-plans"]}
    out, companies, missing = [], collections.Counter(), 0
    for fn, typ in [("standard-plans.json", "S"), ("flexi-plans.json", "F")]:
        for p in json.loads((RAW / fn).read_text("utf-8"))["certified-plans"]:
            if not active(p):
                continue
            comp = p["company-name"]["zh-hk"]
            for v in p["plan-info-certified"]:
                if not active(v):
                    continue
                c = v["certification-no"]
                pr = prem.get(c)
                if not pr:
                    missing += 1
                    continue
                lv = v["plan-level"]["zh-hk"]
                ded, dcur, room, region = parse_level(lv)
                if typ == "S":
                    ded, dcur = 0, "HKD"
                tables, basis = {}, "S"
                for g in "MF":
                    for s in "NY":
                        t = pr["premium"].get("S" + g + s) or pr["premium"].get("R" + g + s)
                        if not pr["premium"].get("S" + g + s):
                            basis = "R"
                        if not t:
                            continue
                        mx = max(int(a) for a in t)
                        arr = [t.get(str(a)) for a in range(mx + 1)]
                        tables[g + s] = [None if x is None else round(x) for x in arr]
                if not tables:
                    continue
                companies[comp] += 1
                out.append({
                    "id": c, "t": typ, "co": short(comp), "cof": comp,
                    "n": p["plan-name"]["zh-hk"], "lv": lv, "cur": pr["currency"],
                    "ded": ded, "dcur": dcur, "room": room, "rg": region,
                    "b": basis, "am": pr["age-counting-method"], "pd": pr["prem-date"],
                    "doc": BASE + v["premium-doc-url"]["zh-hk"],
                    "pdoc": BASE + v["plan-doc-url"]["zh-hk"],
                    "p": tables,
                })
    if len(out) < 100:
        sys.exit(f"整理後只得 {len(out)} 個計劃，數據可能有問題，今次唔更新網站。")
    meta = {
        "plans": len(out), "insurers": len(companies),
        "families": len({(o["cof"], o["n"]) for o in out}),
        "latest": max(o["pd"] for o in out),
    }
    print("整理完成：", meta, f"（{missing} 個版本搵唔到保費，已略過）")
    return {"meta": meta, "plans": out}


# ---------- 砌網頁 ----------
def build_site(data):
    tpl = (ROOT / "src" / "template.html").read_text("utf-8")
    head, body = tpl.split('<header class="bar">', 1)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    body = '<header class="bar">' + body.replace("__DATA__", payload)
    html = (
        '<!doctype html>\n<html lang="zh-HK">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        f'<link rel="canonical" href="{SITE_URL}/">\n'
        '<meta property="og:type" content="website">\n'
        '<meta property="og:title" content="vhiswiki 自願醫保百科">\n'
        f'<meta property="og:description" content="按年齡即時比較全港 {data["meta"]["plans"]} 個在售自願醫保計劃版本保費，數據來自政府開放數據。">\n'
        f'<meta property="og:url" content="{SITE_URL}/">\n'
        '<style>body{margin:0}img{max-width:100%}</style>\n'
        + head + "</head>\n<body>\n" + body + "\n</body>\n</html>\n"
    )
    SITE.mkdir(exist_ok=True)
    (SITE / "index.html").write_text(html, "utf-8")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", "utf-8")
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{SITE_URL}/</loc></url></urlset>\n", "utf-8")
    cname = ROOT / "CNAME"
    if cname.exists():
        (SITE / "CNAME").write_text(cname.read_text("utf-8"), "utf-8")
    print(f"已建立 site/index.html（{len(html) // 1024} KB）")


if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    if "--offline" not in sys.argv:
        download()
    build_site(build_data())
