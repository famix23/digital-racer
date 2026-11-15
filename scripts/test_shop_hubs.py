#!/usr/bin/env python3
"""Guard canonical shop pages, current inventory links, category content, and sitemap inclusion."""
from html import unescape
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOST = "https://www.digitalracer.store"

def main():
    config = json.loads((ROOT / "content/shop-hubs.json").read_text(encoding="utf-8"))
    raw = json.loads((ROOT / "inventory.json").read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else raw["items"]
    manifest = json.loads((ROOT / "p/index.json").read_text(encoding="utf-8"))
    assert len(items) == len(manifest), "Inventory and product manifest must match"
    sitemap = ET.parse(ROOT / "sitemap.xml")
    urls = {node.find("{*}loc").text for node in sitemap.findall("{*}url")}
    assert len(config) == 6 and len({h["slug"] for h in config}) == 6
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    catalog = (ROOT / "catalog.html").read_text(encoding="utf-8")
    for hub in config:
        slug = hub["slug"]
        target = "/shop/" + slug + "/"
        canonical = HOST + target
        page = (ROOT / "shop" / slug / "index.html").read_text(encoding="utf-8")
        assert canonical in urls, (slug, "sitemap")
        assert '<link rel="canonical" href="' + canonical + '">' in page, (slug, "canonical")
        assert '<meta name="robots" content="index,follow">' in page, (slug, "indexability")
        assert 'name="description"' in page and hub["description"] in page, (slug, "summary")
        assert page.count("<h1>") == 1, (slug, "one h1")
        assert page.count("adsbygoogle.js") == 1, (slug, "one ad client")
        # Visible shopping categories must open actual filtered product listings.
        from urllib.parse import quote
        real_category = "/catalog?category=" + quote(hub["category"], safe="")
        assert 'href="' + real_category + '"' in home, (slug, "category link should open catalog")
        assert 'data-filter="' + hub["category"] + '"' in catalog, (slug, "catalog filter missing")
        scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, flags=re.S)
        assert len(scripts) == 1, (slug, "schema")
        schema = json.loads(scripts[0])
        assert schema["@type"] == "CollectionPage" and schema["url"] == canonical
        expected = [manifest[i]["url"] for i, item in enumerate(items) if item["category"] == hub["category"]][-12:][::-1]
        # All current category products have direct HTML links from the hub.
        all_category = [manifest[i] for i, item in enumerate(items) if item["category"] == hub["category"]]
        featured_set = set(expected)
        remaining = [x for x in all_category if x["url"] not in featured_set]
        directory_urls = re.findall(r'<a class="directory-product" href="([^"]+)"', page)
        assert directory_urls == [x["url"] for x in remaining], (slug, "full directory out of date")
        assert len(set(expected + directory_urls)) == len(all_category), (slug, "directory missing product")
        actual = re.findall(r'<a class="product-card" href="([^"]+)"', page)
        assert expected == actual, (slug, "stale product list", expected, actual)
        schema_urls = [x["url"] for x in schema["mainEntity"]["itemListElement"]]
        assert schema_urls == [HOST + route for route in expected], (slug, "structured links")
        body = page.split("<main", 1)[1].split("</main>", 1)[0]
        plain = unescape(re.sub(r"<[^>]+>", " ", body))
        assert len(plain.split()) >= 300, (slug, "thin hub page")
        assert "noindex" not in page.lower(), (slug, "unexpected noindex")
        for linked in config:
            if linked["slug"] != slug:
                assert 'href="/shop/' + linked["slug"] + '/"' in page, (slug, "missing category crosslink")
    print(f"Passed: {len(config)} canonical category hubs, metadata, internal navigation, real products and sitemap links.")

if __name__ == "__main__":
    main()
