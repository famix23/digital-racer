#!/usr/bin/env python3
"""Guard ten image-backed original Bentley V4.7 enquiries without inventing stock."""
from pathlib import Path
from html import unescape
import json
import re

ROOT = Path(__file__).resolve().parents[1]
inventory = json.loads((ROOT / "inventory.json").read_text(encoding="utf-8"))["items"]
manifest = json.loads((ROOT / "p/index.json").read_text(encoding="utf-8"))
assert len(inventory) == len(manifest), "Regenerate all static pages after catalog changes"
cards = [
    (row, manifest[i]) for i, row in enumerate(inventory)
    if str(row.get("supplier_listing_id", "")).startswith("dr-original-bentley-v47-promo-")
]
assert len(cards) == 10, "Exactly ten original Bentley V4.7 promo cards required"
assert len({row["title"] for row, _ in cards}) == 10
assert len({row["thumbnail"] for row, _ in cards}) == 10
assert len({row["price"] for row, _ in cards}) == 10
for row, listing in cards:
    title = row["title"]
    assert row["category"] == "Car Card" and row["listing_origin"] == "original", title
    assert row.get("availability_unverified") is True, title
    assert "source_title" not in row, title
    assert "PUBG Mobile" in title and "Bentley" in title and "V4.7" in title, title
    assert 90 <= float(row["price"]) <= 270, title
    desc = row["description"]
    assert len(desc) >= 1600 and desc.count("2026") >= 2, title
    for phrase in ("November 20, 2026", "AI-generated", "confirm", "PUBG Mobile", "region", "gift"):
        assert phrase.lower() in desc.lower(), (title, phrase)
    image = ROOT / row["thumbnail"].lstrip("/")
    assert image.is_file() and image.stat().st_size > 40000, (title, image)
    assert image.read_bytes()[:4] == b"RIFF" and image.suffix == ".webp", image
    assert listing["title"] == title and listing["thumbnail"] == row["thumbnail"], title
    page = (ROOT / listing["url"].lstrip("/") / "index.html").read_text(encoding="utf-8")
    assert '<h1 class="main-title" id="prod-title">' + title + '</h1>' in unescape(page), title
    assert 'Confirm timeframe</span>' in page, title
    assert "https://wa.me/923454342911" in page, title
    assert "availability" not in json.loads(re.search(
        r'<script type="application/ld\\+json">\\s*({[^<]+})\\s*</script>', page
    ).group(1)).get("offers", {}), title
print("Passed: 10 distinct Bentley promo cards with original image bytes, deep source-aware copy, prices, enquiry checkout and no invented stock claims.")
