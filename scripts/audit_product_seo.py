#!/usr/bin/env python3
"""Audits every built product page for SEO and purchasing integrity.

Offline validation: this does not prove Google has indexed any URL or that
the images are reachable through an upstream CDN; live URL tests are separate.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOST = "https://www.digitalracer.store"
TOP = 22

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_depth = 0
        self.title = []
        self.metas = defaultdict(list)
        self.canonicals = []
        self.headings = []
        self.images = []
        self.buy_links = []
        self.related = []
        self.scripts = []
        self._json_ld = False
        self._json_buf = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "title":
            self.title_depth += 1
        if tag == "meta":
            key = attrs.get("name") or attrs.get("property")
            if key:
                self.metas[key.lower()].append(attrs.get("content", ""))
        if tag == "link" and attrs.get("rel", "").lower() == "canonical":
            self.canonicals.append(attrs.get("href", ""))
        if tag == "img":
            self.images.append(attrs)
        if tag == "h1":
            self.headings.append(attrs)
        if tag == "a":
            if attrs.get("id") == "buy-btn":
                self.buy_links.append(attrs.get("href", ""))
            if attrs.get("class", "") == "rel-card":
                self.related.append(attrs.get("href", ""))
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self._json_ld = True
            self._json_buf = []

    def handle_data(self, data):
        if self.title_depth:
            self.title.append(data)
        if self._json_ld:
            self._json_buf.append(data)

    def handle_endtag(self, tag):
        if tag == "title" and self.title_depth:
            self.title_depth -= 1
        if tag == "script" and self._json_ld:
            try:
                self.scripts.append(json.loads("".join(self._json_buf)))
            except (ValueError, TypeError) as e:
                self.scripts.append({"__invalid__": str(e)})
            self._json_ld = False

def page_for(url: str) -> Path:
    return ROOT / url.strip("/") / "index.html"

def plain(s: str) -> str:
    return re.sub(r"\s+", " ", unescape(str(s))).strip()

def main():
    inventory = json.loads((ROOT / "inventory.json").read_text(encoding="utf-8"))
    items = inventory if isinstance(inventory, list) else inventory["items"]
    manifest = json.loads((ROOT / "p/index.json").read_text(encoding="utf-8"))
    sitemap = ET.parse(ROOT / "sitemap.xml")
    sitemap_urls = {n.find("{*}loc").text for n in sitemap.findall("{*}url")}
    failures, warnings = [], []
    title_count, description_count = Counter(), Counter()
    counts = Counter()
    missing_local_image_files = []
    buy_count = image_count = offers_count = 0

    if len(manifest) != len(items):
        failures.append(f"Manifest/inventory count mismatch: {len(manifest)} vs {len(items)}")

    for n, (product, item) in enumerate(zip(manifest, items)):
        label = product.get("url", str(n))
        file = page_for(label)
        if not file.is_file():
            failures.append(f"{label}: generated HTML page absent")
            continue
        page = Page()
        page.feed(file.read_text(encoding="utf-8"))
        title = plain("".join(page.title))
        descriptions = page.metas["description"]
        description = plain(descriptions[0]) if descriptions else ""
        title_count[title] += 1
        description_count[description] += 1
        if not title or len(title) < 20:
            failures.append(f"{label}: missing or unusually short document title")
        if not description or len(description) < 45:
            warnings.append(f"{label}: thin/missing SEO meta description ({len(description)} chars)")
        if len(description) > 175:
            warnings.append(f"{label}: long SEO meta description ({len(description)} chars)")
        if len(title) > 78:
            warnings.append(f"{label}: long document title ({len(title)} chars)")
        url = HOST + label
        if page.canonicals != [url]:
            failures.append(f"{label}: incorrect/multiple self-canonical tags")
        if url not in sitemap_urls:
            failures.append(f"{label}: absent from sitemap")
        if any("noindex" in value.lower() for value in page.metas["robots"] + page.metas["googlebot"]):
            failures.append(f"{label}: noindex on product page")
        if len(page.headings) != 1:
            failures.append(f"{label}: expected one product h1, found {len(page.headings)}")
        if len(page.metas["og:title"]) != 1 or len(page.metas["og:description"]) != 1:
            failures.append(f"{label}: missing/duplicate OG title/description")
        if len(page.metas["twitter:card"]) != 1:
            failures.append(f"{label}: missing Twitter card metadata")

        products = [x for x in page.scripts if x.get("@type") == "Product"]
        if len(products) != 1:
            failures.append(f"{label}: expected one Product JSON-LD object, got {len(products)}")
            continue
        ld = products[0]
        if ld.get("url") != url or ld.get("name") != plain(item.get("title", ""))[:150]:
            # Decorative symbols may intentionally be normalized in schema.
            if ld.get("url") != url or not ld.get("name"):
                failures.append(f"{label}: incomplete Product JSON-LD name or URL")
        if not ld.get("description"):
            failures.append(f"{label}: missing Product JSON-LD description")
        images = ld.get("image", [])
        if not isinstance(images, list) or not images:
            failures.append(f"{label}: no structured product image")
        else:
            image_count += 1
        for image in images:
            p = urlsplit(image)
            if p.netloc == "www.digitalracer.store":
                local = ROOT / unquote(p.path).lstrip("/")
                if not local.is_file():
                    missing_local_image_files.append((label, image))
            elif p.scheme != "https":
                failures.append(f"{label}: image uses insecure/invalid URL {image}")
        price = ld.get("offers", {}).get("price")
        if ld.get("offers", {}).get("priceCurrency") != "USD":
            failures.append(f"{label}: offer must use actual USD currency")
        try:
            expected = Decimal(str(product.get("price")).replace(",", "").replace("$", ""))
            actual = Decimal(str(price))
            if expected != actual:
                failures.append(f"{label}: structured price {price} != listing {expected}")
            else:
                offers_count += 1
        except (InvalidOperation, TypeError):
            failures.append(f"{label}: unreadable price {price}")
        if not page.buy_links and not item.get("reference_only"):
            failures.append(f"{label}: no Buy Now anchor in pre-rendered HTML")
        elif page.buy_links:
            if len(page.buy_links) != 1 or not page.buy_links[0].startswith("https://wa.me/"):
                failures.append(f"{label}: missing/invalid WhatsApp checkout link")
            else:
                buy_count += 1
        if not any(img.get("alt", "").strip() and img.get("src") for img in page.images):
            failures.append(f"{label}: product does not have an HTML image with alt text")
        if len(page.related) != min(4, len(manifest) - 1):
            failures.append(f"{label}: expected four static related-product links")

        raw_description = plain(item.get("description", ""))
        if len(raw_description) < 100:
            warnings.append(f"{label}: source description is brief ({len(raw_description)} chars)")
        counts[item.get("category", "unknown")] += 1

    for title, count in title_count.items():
        if count > 1:
            warnings.append(f"Duplicate <title> across {count} product pages: {title[:100]}")
    for desc, count in description_count.items():
        if count > 1:
            warnings.append(f"Duplicate meta description across {count} product pages: {desc[:100]}")
    for name, url in missing_local_image_files:
        failures.append(f"{name}: Product image file not in published static source: {url}")

    print(f"PRODUCT_SEO_REPORT product_count={len(items)} meta_titles={len(title_count)} unique_descriptions={len(description_count)}")
    print(f"PRODUCT_SEO_REPORT structured_offers_priced={offers_count} product_schema_with_image={image_count} whatsapp_links={buy_count}")
    print(f"PRODUCT_SEO_REPORT categories={dict(counts)}")
    print(f"PRODUCT_SEO_REPORT warnings={len(warnings)} errors={len(failures)}")
    for msg in warnings[:TOP]:
        print("SEO_WARNING " + msg)
    if len(warnings) > TOP:
        print(f"SEO_WARNING and {len(warnings)-TOP} more; see repository audit to prioritize.")
    for msg in failures[:80]:
        print("SEO_ERROR " + msg)
    if failures:
        raise SystemExit(f"Product SEO audit failed on {len(failures)} issues.")
    print("Passed: all product pages have valid canonical/metadata/structured prices/checkout links and local image files.")

if __name__ == "__main__":
    main()
