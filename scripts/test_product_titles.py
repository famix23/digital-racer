#!/usr/bin/env python3
"""Validate exact supplier-visible titles and natural SEO context for each product."""
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
cms = (ROOT / "admin/config.yml").read_text(encoding="utf-8")
assert 'name: "original_title"' in cms, "CMS must expose original seller title corrections"
assert 'name: "title"' in cms, "CMS title input required"
source = json.loads((ROOT / "inventory.json").read_text(encoding="utf-8"))
products = source if isinstance(source, list) else source["items"]
manifest = json.loads((ROOT / "p/index.json").read_text(encoding="utf-8"))
overrides = json.loads((ROOT / "content/product-title-overrides.json").read_text(encoding="utf-8"))
assert len(products) == len(manifest)
assert all(isinstance(k, str) and isinstance(v, str) and v.strip() for k, v in overrides.items())
assert set(overrides).issubset({str(p["title"]).strip() for p in products}), "Override key has no product"
key = "PUBG Mobile Old Account – Fireman Set, 4x Red Loot Crate Max, 2 Sports Cars, 23 Kill Msgs"
assert overrides.get(key) == "Fireman Set, 4x Red Loot Crate Max, 2 Sports Cars, 23 Kill Msgs"
safe_categories = {"Account", "Car Card", "UC Top-Up", "Rank Boosting", "Popularity"}
for p, mapping in zip(products, manifest):
    title = str(p["title"]).strip()
    assert mapping["title"] == title, "Original listing identity changed"
    original = next((p.get(k) for k in ("original_title", "source_title", "seller_title")
                     if isinstance(p.get(k), str) and p.get(k).strip()), None)
    displayed = original if original is not None else overrides.get(title, title)
    file = ROOT / mapping["url"].strip("/") / "index.html"
    page = file.read_text(encoding="utf-8")
    heading = re.search(r'<h1 class="main-title" id="prod-title">(.*?)</h1>', page, re.S)
    assert heading and html.unescape(heading.group(1)) == displayed, (mapping["url"], "visible title")
    canonical = "https://www.digitalracer.store" + mapping["url"]
    assert '<link rel="canonical" href="' + canonical + '">' in page, mapping["url"]
    blocks = re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', page)
    jsonld = [json.loads(block) for block in blocks]
    product_schema = next((item for item in jsonld if item.get("@type") == "Product"), None)
    assert product_schema and product_schema["name"] == displayed, (mapping["url"], "schema title")
    description = str(p.get("description") or "")
    category = p.get("category")
    schema_description = product_schema["description"]
    if category in safe_categories:
        if "pubg mobile" in description.casefold():
            assert not schema_description.startswith("PUBG Mobile " + category + ". "), (mapping["url"], "duplicate keyword")
        else:
            assert schema_description.startswith("PUBG Mobile "), (mapping["url"], "missing category keyword")
    if category == "In-Game Items" and "pubg mobile" not in description.casefold():
        assert not schema_description.startswith("PUBG Mobile In-Game Item."), mapping["url"]
print("Passed: %d canonical product titles, supplier data preservation and conditional SEO descriptions." % len(products))
