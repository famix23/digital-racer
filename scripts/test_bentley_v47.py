#!/usr/bin/env python3
"""Verify the 10 Bentley V4.7 listings use normal Buy Now ordering, real prices and transparent artwork."""
from pathlib import Path
from html import unescape
import json
import re

ROOT = Path(__file__).resolve().parents[1]
inventory = json.loads((ROOT / "inventory.json").read_text(encoding="utf-8"))["items"]
manifest = json.loads((ROOT / "p/index.json").read_text(encoding="utf-8"))
assert len(inventory) == len(manifest), "Regenerate static pages after catalog changes"
cards = [(row, manifest[i]) for i, row in enumerate(inventory)
         if str(row.get("supplier_listing_id", "")).startswith("dr-original-bentley-v47-promo-")]
assert len(cards) == 10, "Exactly 10 Bentley V4.7 cards required"
assert len({row["title"] for row, _ in cards}) == len(cards)
assert len({row["thumbnail"] for row, _ in cards}) == len(cards)
assert len({row["price"] for row, _ in cards}) == len(cards)
for row, listing in cards:
    title = row["original_title"]
    assert row["category"] == "Car Card" and row["listing_origin"] == "original"
    assert not row.get("availability_unverified") and not row.get("reference_only")
    assert row["badge"] == "Bentley 4.7" and row["tag"] == "BENTLEY V4.7"
    assert "PUBG Mobile" in title and "Bentley" in title and "V4.7" in title
    assert 90 <= float(row["price"]) <= 270
    desc = row["description"]
    assert len(desc) >= 1100 and "Buy Now" in desc and "promotional artwork" in desc
    for banned in ("pre-launch", "enquiry", "check availability", "not available", "confirm", "demo"):
        assert banned not in (title + " " + desc).lower(), (title, banned)
    file = ROOT / row["thumbnail"].lstrip("/")
    assert file.is_file() and file.stat().st_size > 40000 and file.read_bytes()[:4] == b"RIFF"
    assert listing["title"] == row["title"] and listing["thumbnail"] == row["thumbnail"]
    page = (ROOT / listing["url"].lstrip("/") / "index.html").read_text(encoding="utf-8")
    assert '<h1 class="main-title" id="prod-title">' + title + '</h1>' in unescape(page), title
    button = re.search(r'<a [^>]*id="buy-btn"[^>]*>(.*?)</a>', page, flags=re.S)
    assert button and "Buy Now" in button.group(1) and "Check Availability" not in button.group(1)
    desc_html = re.search(r'<div class="desc-content" id="prod-desc">(.*?)</div>', page, flags=re.S)
    assert desc_html and "Pre-launch enquiry:" not in desc_html.group(1)
    assert '<span>Confirm timeframe</span>' not in page.split('<script>window.DR_PRESET')[0]
    assert "https://wa.me/923454342911" in page
    assert ("I%20want%20to%20acquire" in page or "I%20want%20to%20acquire" in unescape(page))
    scripts = re.findall(r'<script type="application/ld\+json">\s*({[^<]+})\s*</script>', page)
    product = next((json.loads(script) for script in scripts if json.loads(script).get("@type") == "Product"), None)
    assert product and product["name"] == title
    assert product["offers"]["availability"] == "https://schema.org/InStock"
print("Passed: 10 distinct Bentley V4.7 products with Buy Now, unchanged URLs, images and prices.")
