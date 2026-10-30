#!/usr/bin/env python3
"""Validate AdSense HTML placement and ads.txt; --live checks production."""
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
CLIENT = "ca-pub-3636750354534911"
SRC = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + CLIENT
RECORD = "google.com, pub-3636750354534911, DIRECT, f08c47fec0942fa0"

class HeadCheck(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_head = False
        self.loaders = []
    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self.in_head = True
        attrs = dict(attrs)
        if tag == "script" and "adsbygoogle.js" in attrs.get("src", ""):
            self.loaders.append((self.in_head, attrs))
    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False

def check_html(text, label):
    parser = HeadCheck()
    parser.feed(text)
    assert len(parser.loaders) == 1, (label, "expected exactly one AdSense loader")
    in_head, attrs = parser.loaders[0]
    assert in_head and attrs.get("src") == SRC, (label, "wrong head placement or publisher")
    assert "async" in attrs and attrs.get("crossorigin") == "anonymous", label

if "--live" in sys.argv:
    host = "https://www.digitalracer.store"
    manifest = json.loads((ROOT / "p/index.json").read_text())
    urls = ["/", "/catalog", "/product", "/about/", "/contact/", "/terms/", "/privacy/"]
    urls += [p["url"] for p in manifest]
    for url in urls:
        with urlopen(host + url, timeout=30) as response:
            assert response.status == 200, url
            assert "text/html" in response.headers.get("Content-Type", ""), url
            check_html(response.read().decode(), url)
    with urlopen(host + "/ads.txt", timeout=30) as response:
        assert response.status == 200
        assert "text/plain" in response.headers.get("Content-Type", "")
        assert response.read().decode().strip() == RECORD
    print(f"Passed live AdSense checks for {len(urls)} pages and ads.txt.")
else:
    pages = list(ROOT.rglob("*.html"))
    pages = [p for p in pages if not any(x in p.parts for x in (".git", "node_modules", ".wrangler"))]
    for page in pages:
        check_html(page.read_text(encoding="utf-8"), str(page.relative_to(ROOT)))
    assert (ROOT / "ads.txt").read_text().strip() == RECORD
    print(f"Passed AdSense checks for {len(pages)} HTML files and ads.txt.")
