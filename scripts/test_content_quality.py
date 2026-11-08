#!/usr/bin/env python3
"""Checks for useful, indexable, reachable editorial pages; not an AdSense approval test."""
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://www.digitalracer.store"
GUIDES = (
    "guides/",
    "guides/pubg-mobile-account-safety/",
    "guides/pubg-mobile-uc-top-up-safety/",
    "guides/pubg-mobile-skins-explained/",
)

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.main = False
        self.ignore = False
        self.h1 = 0
        self.canonical = []
        self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "main":
            self.main = True
        if tag == "h1":
            self.h1 += 1
        if tag in ("style", "script"):
            self.ignore = True
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical.append(attrs.get("href"))
        if tag == "a":
            self.links.append(attrs.get("href", ""))
    def handle_endtag(self, tag):
        if tag == "main":
            self.main = False
        if tag in ("style", "script"):
            self.ignore = False
    def handle_data(self, data):
        if self.main and not self.ignore:
            self.text.append(data)

sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
for url in GUIDES:
    path = ROOT / url / "index.html"
    assert path.exists(), url
    parser = Page()
    parser.feed(path.read_text(encoding="utf-8"))
    assert parser.h1 == 1, (url, "one h1 required")
    assert parser.canonical == [BASE + "/" + url], (url, "bad canonical")
    assert f"<loc>{BASE}/{url}</loc>" in sitemap, (url, "missing from sitemap")
    assert any(link == "/catalog" for link in parser.links), (url, "catalog link")
    count = len(re.findall(r"\b[\w'-]+\b", " ".join(parser.text)))
    assert count >= (180 if url == "guides/" else 500), (url, "thin article", count)
for path in ("index.html", "catalog.html", "about/index.html"):
    data = (ROOT / path).read_text(encoding="utf-8")
    assert 'href="/guides/"' in data, (path, "missing guides navigation")
print("Passed: four indexable guide pages, canonical URLs, sitemap, substantive text and navigation.")

# Blog posts are generated from independent source files, never from inventory.json.
from build_blog import load_posts
blog_posts = load_posts(ROOT)
blog_urls = ["blog/"] + ["blog/" + p["slug"] + "/" for p in blog_posts]
for url in blog_urls:
    page = (ROOT / url / "index.html").read_text(encoding="utf-8")
    parser = Page()
    parser.feed(page)
    assert "BLOG:GENERATED" in page, url
    assert parser.h1 == 1, url
    assert parser.canonical == [BASE + "/" + url], url
    assert f"<loc>{BASE}/{url}</loc>" in sitemap, url
    assert "/blog/" in parser.links and "/guides/" in parser.links and "/catalog" in parser.links, url
    assert all(link.startswith("/") and not link.startswith("//") or link.startswith("#") for link in parser.links), (url, "outbound links not allowed")
    count = len(re.findall(r"\b[\w'-]+\b", " ".join(parser.text)))
    assert count >= (45 if url == "blog/" else 450), (url, count)
for url in GUIDES:
    parser = Page()
    parser.feed((ROOT / url / "index.html").read_text(encoding="utf-8"))
    assert all(link.startswith("/") and not link.startswith("//") or link.startswith("#") for link in parser.links), (url, "outbound links not allowed")
print(f"Passed: {len(blog_urls)} blog pages, safe site-only links and existing guides.")
