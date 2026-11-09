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
# Every article must expose the date and publisher metadata from its editorial source.
import json
for post in blog_posts:
    url = "blog/" + post["slug"] + "/"
    article = (ROOT / url / "index.html").read_text(encoding="utf-8")
    schemas = re.findall(r'<script type="application/ld\\+json">(.*?)</script>',
                         article, flags=re.S)
    assert len(schemas) == 1, (url, "expected one BlogPosting schema")
    schema = json.loads(schemas[0])
    assert schema["@type"] == "BlogPosting", url
    assert schema["headline"] == post["title"], url
    assert schema["description"] == post["summary"], url
    assert schema["datePublished"] == post["published"], url
    assert schema["mainEntityOfPage"] == BASE + "/" + url, url
    assert schema["author"]["name"] == "Digital Racer", url
    assert schema["publisher"]["name"] == "Digital Racer", url
    assert '<time datetime="' + post["published"] + '">' in article, url

print(f"Passed: {len(blog_urls)} blog pages, safe site-only links and existing guides.")

# Related guide links are generated from explicit article topic metadata.
from build_related_guides import TARGETS, START, END, relevant
for rel, _, _, _, topics, limit in TARGETS:
    markup = (ROOT / rel).read_text(encoding="utf-8")
    assert markup.count(START) == 1 and markup.count(END) == 1, rel
    expected = relevant(blog_posts, topics, limit)
    generated = markup.split(START, 1)[1].split(END, 1)[0]
    actual = re.findall(r'href="(/blog/[^"]+/)"', generated)
    wanted = ["/blog/" + p["slug"] + "/" for p in expected]
    assert actual == wanted, (rel, actual, wanted)
    assert len(actual) == len(set(actual)), (rel, "duplicate related links")
    assert all(link.startswith("/") and not link.startswith("//") for link in actual), rel
# The guides landing page should expose every current tutorial in its related directory.
tutorials = relevant(blog_posts, ("tutorial",))
assert tutorials, "No tutorial articles are discoverable from the guides directory"
assert len(re.findall(r'href="(/blog/[^"]+/)"', (ROOT / "guides/index.html").read_text(encoding="utf-8"))) >= len(tutorials)
print(f"Passed: automatic topic-based guide links in {len(TARGETS)} guide pages.")
