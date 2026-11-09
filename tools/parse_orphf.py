"""將抓返嚟嘅醫院賬單統計 HTML 整理成 data/surgery-bills.json"""
import json, re, sys
from pathlib import Path

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
HOSP = ["Canossa Hospital (Caritas)", "Gleneagles Hospital Hong Kong", "Hong Kong Adventist Hospital - Stubbs Road",
        "Hong Kong Sanatorium & Hospital Limited", "Matilda & War Memorial Hospital", "St. Paul's Hospital",
        "Evangel Hospital", "Hong Kong Baptist Hospital", "Precious Blood Hospital (Caritas)", "St. Teresa's Hospital",
        "CUHK Medical Centre", "Hong Kong Adventist Hospital - Tsuen Wan", "Union Hospital"]
METRICS = {"Average Length of Stay": "los", "Doctor's Fees (HK$)": "doc", "Hospital Charges (HK$)": "hosp",
           "Total Charges (HK$)": "tot", "Annual Number of Discharges (in range)": "n"}


def tokens(f):
    h = f.read_text("utf-8")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", h, flags=re.S)
    t = re.sub(r"<[^>]+>", "\x00", t).replace("&nbsp;", " ").replace("&amp;", "&").replace("&#39;", "'")
    return [x.strip() for x in t.split("\x00") if x.strip()]


def money(x):
    m = re.fullmatch(r"\$\s*([\d,]+)", x)
    return int(m.group(1).replace(",", "")) if m else None


out = []
for f in sorted(SRC.glob("*.html")):
    tk = tokens(f)
    code = f.stem
    blocks = [i for i, x in enumerate(tk) if x.startswith("Statistics of ")]
    for bi, start in enumerate(blocks):
        end = blocks[bi + 1] if bi + 1 < len(blocks) else len(tk)
        title = tk[start][len("Statistics of "):].strip()
        setting = "inpatient" if "(In-patient)" in title else "day"
        name = title.replace("(In-patient)", "").replace("(Day Case)", "").strip()
        rows = {}
        metric = None
        i = start
        while i < end:
            x = tk[i]
            if x in METRICS:
                metric = METRICS[x]
            elif metric and x in HOSP or (metric and any(x.startswith(h) for h in HOSP)):
                hosp = next(h for h in HOSP if x.startswith(h))
                j = i + 1
                while j < end and any(tk[j].startswith(h) for h in HOSP) and tk[j].startswith(hosp):
                    j += 1
                ptype = ""
                if j < end and not tk[j].startswith("$") and not re.match(r"[\d>]", tk[j]):
                    ptype = tk[j]
                    j += 1
                    if j < end and tk[j] == ptype:
                        j += 1
                key = (hosp, ptype)
                r = rows.setdefault(key, {})
                if metric in ("doc", "hosp", "tot"):
                    a, b = money(tk[j]) if j < end else None, money(tk[j + 1]) if j + 1 < end else None
                    if a is not None:
                        r[metric] = [a, b]
                elif metric == "los":
                    m = re.match(r"([\d.]+)", tk[j]) if j < end else None
                    if m:
                        r["los"] = float(m.group(1))
                i = j
                continue
            i += 1
        for (hosp, ptype), r in rows.items():
            if "tot" in r or "doc" in r:
                out.append({"code": code, "name": name, "setting": setting, "type": ptype, "hospital": hosp, **r})
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=0), "utf-8")
print(len(out), "rows")
