"""下載 tools/fetch_urls.txt 列出嘅網頁或 PDF，存到 fetched 分支（研究用）。"""
import hashlib, re, subprocess, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fetched"
OUT.mkdir(exist_ok=True)
for line in (ROOT / "tools/fetch_urls.txt").read_text("utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    name, url = line.split(" ", 1) if " " in line else (hashlib.md5(line.encode()).hexdigest()[:8], line)
    url = url.strip()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"})
        body = urllib.request.urlopen(req, timeout=90).read()
        is_pdf = body[:4] == b"%PDF"
        f = OUT / (name + (".pdf" if is_pdf else ".html"))
        f.write_bytes(body)
        if is_pdf:
            subprocess.run(["pdftotext", "-layout", str(f), str(OUT / (name + ".txt"))], check=False)
        print("OK", name, len(body))
    except Exception as e:
        (OUT / (name + ".error")).write_text(str(e), "utf-8")
        print("FAIL", name, e)
