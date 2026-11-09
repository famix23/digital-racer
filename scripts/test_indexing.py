#!/usr/bin/env python3
"""Audit indexable static pages, redirects and internal links.

Run after build_seo.py. This checks checked-in files, not HTTP response codes
or URL Inspection results on the deployed website.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOST = "https://www.digitalracer.store"

class Tags(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonicals, self.robots, self.links = [], [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and attrs.get("rel", "").lower() == "canonical":
            self.canonicals.append(attrs.get("href", ""))
        if tag == "meta" and attrs.get("name", "").lower() in ("robots", "googlebot"):
            self.robots.append(attrs.get("content", "").lower())
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

def page_for(url_path):
    route = unquote(url_path).rstrip("/")
    if not route:
        return ROOT / "index.html"
    route = route.lstrip("/")
    if route in ("catalog", "product"):
        return ROOT / (route + ".html")
    if route.endswith(".html") or "." in Path(route).name:
        return ROOT / route
    return ROOT / route / "index.html"

def parse(path):
    p = Tags()
    p.feed(path.read_text(encoding="utf-8"))
    return p

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def main():
    sitemap = ET.parse(ROOT / "sitemap.xml")
    urls = [e.find("{*}loc").text for e in sitemap.findall("{*}url")]
    require(urls and len(urls) == len(set(urls)), "Empty sitemap or duplicate URL")
    routes = set()
    for full in urls:
        u = urlsplit(full)
        require(u.scheme + "://" + u.netloc == HOST, f"Incorrect sitemap host: {full}")
        require(not u.query and not u.fragment, f"Noncanonical sitemap URL: {full}")
        require(u.path not in routes, f"Duplicate route: {u.path}")
        routes.add(u.path)
        filename = page_for(u.path)
        require(filename.is_file(), f"Sitemap page missing: {full} -> {filename}")
        page = parse(filename)
        require(page.canonicals == [full], f"Wrong self-canonical: {filename}")
        require(not any(re.search(r"\bnoindex\b|\bnone\b", tag) for tag in page.robots),
                f"Sitemap page marked noindex: {filename}")

    # The sitemap should identify meaningful editorial update dates, not invent
    # change dates for products without reliable versioned source metadata.
    from build_blog import load_posts
    editorial_dates = {
        "/blog/" + post["slug"] + "/": post.get("modified", post["published"])
        for post in load_posts(ROOT)
    }
    for entry in sitemap.findall("{*}url"):
        loc = entry.find("{*}loc").text
        route = urlsplit(loc).path
        lastmod = entry.find("{*}lastmod")
        if route in editorial_dates:
            require(lastmod is not None and lastmod.text == editorial_dates[route],
                    f"Missing or inaccurate editorial lastmod: {route}")
        else:
            require(lastmod is None, f"Unverified lastmod date on {route}")

    manifest = json.loads((ROOT / "p/index.json").read_text(encoding="utf-8"))
    products = {p["url"] for p in manifest}
    sitemap_products = {x for x in routes if x.startswith("/p/")}
    require(products == sitemap_products,
            f"Product pages missing/extra in sitemap: {sorted(products ^ sitemap_products)[:10]}")

    rules = {}
    for line in (ROOT / "_redirects").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split()
        require(len(fields) == 3 and fields[2] == "301", f"Invalid redirect rule: {line}")
        source, dest, _ = fields
        require(source not in rules, f"Duplicate redirect: {source}")
        require(source not in routes, f"Redirect shadows indexed URL: {source}")
        require(dest in routes, f"Redirect target missing from sitemap: {line}")
        rules[source] = dest
    for source, target in rules.items():
        if source.endswith("/"):
            stub = page_for(source)
            require(stub.is_file(), f"Redirect fallback missing: {source}")
            stub_meta = parse(stub)
            require(any("noindex" in tag for tag in stub_meta.robots),
                    f"Redirect fallback must be noindex: {source}")
            require(stub_meta.canonicals == [HOST + target],
                    f"Redirect fallback canonical wrong: {source}")

    # Deliberate exclusions: utility pages and legacy redirect fallbacks.
    for path in ("404.html", "product.html"):
        require(any("noindex" in tag for tag in parse(ROOT / path).robots),
                f"Expected noindex missing on {path}")
    headers = (ROOT / "_headers").read_text(encoding="utf-8")
    require("/admin/*\n  X-Robots-Tag: noindex" in headers, "Admin X-Robots-Tag missing")
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    require("Sitemap: " + HOST + "/sitemap.xml" in robots, "Wrong robots.txt sitemap")
    require("Disallow: /\n" not in robots, "Global robots.txt block")

    utility = {ROOT / "404.html", ROOT / "product.html", ROOT / "admin/index.html"}
    fallback = {page_for(src) for src in rules if src.endswith("/")}
    known = {page_for(route) for route in routes} | utility | fallback
    html_files = [p for p in ROOT.rglob("*.html")
                  if not any(part.startswith(".") for part in p.relative_to(ROOT).parts)]
    checked_links = 0
    for file in html_files:
        if file.relative_to(ROOT).parts[0] in ("scripts", "tests"):
            continue
        require(file in known, f"Unlisted HTML page: {file}")
        page = parse(file)
        for href in page.links:
            if not href.startswith("/") or href.startswith("//"):
                continue
            target = urlsplit(href).path or "/"
            require(page_for(target).is_file(), f"Broken internal link in {file}: {href}")
            checked_links += 1
            if target.startswith("/p/"):
                require(target in routes or target + "/" in routes
                        or target in rules or target + "/" in rules,
                        f"Product link has no indexable target/redirect: {file}: {href}")

    # Every indexed product receives a crawlable HTML link from another product.
    # This validates the generated files, not merely a JavaScript recommendation.
    incoming = {url: 0 for url in products}
    category_by_url = {}
    inv = json.loads((ROOT / "inventory.json").read_text(encoding="utf-8"))
    inventory = inv if isinstance(inv, list) else inv.get("items", [])
    require(len(inventory) == len(manifest), "Product manifest/inventory length mismatch")
    for item, entry in zip(inventory, manifest):
        require(item["title"] == entry["title"], "Product order changed without rebuilding")
        category_by_url[entry["url"]] = item["category"]
    for entry in manifest:
        url = entry["url"]
        markup = page_for(url).read_text(encoding="utf-8")
        linked = re.findall(r'<a href="(/p/[^"]+/)" class="rel-card"', markup)
        require(len(linked) == min(4, len(products) - 1), f"Wrong related link count: {url}")
        require(len(linked) == len(set(linked)), f"Duplicate related cards: {url}")
        require(url not in linked, f"Product links to itself: {url}")
        same_category = sum(1 for other in inventory if other["category"] == category_by_url[url])
        if same_category >= 5:
            require(all(category_by_url.get(link) == category_by_url[url] for link in linked),
                    f"Unrelated suggestions for a category with sufficient inventory: {url}")
        for target in linked:
            require(target in incoming, f"Related link outside catalog: {url} -> {target}")
            incoming[target] += 1
    require(all(count > 0 for count in incoming.values()),
            f"Product discovery gaps: {sum(count == 0 for count in incoming.values())} pages lack incoming related links")

    print(f"Passed indexing audit: {len(routes)} sitemap URLs, "
          f"{len(products)} products, {len(rules)} redirect rules, "
          f"{len(html_files)} HTML files, {checked_links} internal links.")

if __name__ == "__main__":
    main()
