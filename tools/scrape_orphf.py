"""研究用：由醫務衞生局私家醫院價格透明度網站，逐個手術抓取各醫院歷史賬單統計。"""
import requests, time
from bs4 import BeautifulSoup
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "fetched" / "orphf"
OUT.mkdir(parents=True, exist_ok=True)
URL = "https://apps.orphf.gov.hk/Public/Enquiry/Main.aspx"
s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
try:
    js = s.get("https://apps.orphf.gov.hk/Public/JS/Main.js", timeout=60).text
    (OUT / "Main.js").write_text(js, "utf-8")
except Exception as e:
    print("js fail", e)


def form_state(html):
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    for i in soup.select("input"):
        n = i.get("name")
        if n and i.get("type") in ("hidden", None, "text"):
            data[n] = i.get("value", "")
    procs = [o["value"] for o in soup.select("#ddlDSProcedure option")]
    sel = soup.select_one("#ddlDSHospital") or soup.find("select", id=lambda x: x and "DSHospital" in x)
    hosps = [o["value"] for o in sel.select("option")] if sel else []
    return data, procs, hosps, (sel.get("name") if sel else None)


html = s.get(URL, timeout=60).text
data0, procs, hosps, hname = form_state(html)
print("procs", len(procs), "hosps", hosps, hname)
for code in procs:
    try:
        html = s.get(URL, timeout=60).text
        data, _, _, _ = form_state(html)
        data.update({"ddlDSProcedure": code, "hfDSProcedure": code, "hfDSHospital": ",".join(hosps),
                     "btnDSSearch": "Search"})
        payload = list(data.items())
        if hname:
            payload += [(hname, h) for h in hosps]
        r = s.post(URL, data=payload, timeout=90)
        (OUT / f"{code}.html").write_text(r.text, "utf-8")
        print("OK", code, len(r.text))
    except Exception as e:
        print("FAIL", code, e)
    time.sleep(1)
