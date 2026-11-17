#!/usr/bin/env python3
"""Generate six useful, canonical, crawlable shop category hubs from inventory.

The editorial descriptions live in content/shop-hubs.json. Inventory-driven
cards and counts stay in sync when scripts/build_seo.py runs after catalog edits.
"""
from pathlib import Path
from urllib.parse import quote
import html
import json

SITE = "https://www.digitalracer.store"

def esc(value):
    return html.escape(str(value), quote=True)

def load_hubs(root):
    root = Path(root)
    data = json.loads((root / "content" / "shop-hubs.json").read_text(encoding="utf-8"))
    assert len(data) == 6 and len({x["slug"] for x in data}) == 6, "Expected six unique shop hubs"
    return data

def build_shop_hubs(root, products, write):
    root = Path(root)
    template = (root / "scripts" / "shop_template.html.txt").read_text(encoding="utf-8")
    hubs = load_hubs(root)
    slugs = []
    for hub in hubs:
        slug = hub["slug"]
        matches = [p for p in products if p["category"] == hub["category"]]
        chosen = list(reversed(matches))[:12]
        assert matches, f"Shop category is empty: {slug}"
        featured_urls = {p["url"] for p in chosen}
        remaining = [p for p in matches if p["url"] not in featured_urls]
        directory = (
            '<details class="listing-directory"><summary>Browse the remaining ' +
            str(len(remaining)) + ' ' + esc(hub["category"]) +
            ' listings</summary><ul class="directory-list">' +
            "".join(
                '<li><a class="directory-product" href="' + esc(p["url"]) + '">' +
                esc(p["display_title"]) + '</a><small>' + chr(36) + esc(p["price"]) +
                ' USD</small></li>' for p in remaining
            ) + '</ul></details>'
        ) if remaining else ""
        canonical = SITE + "/shop/" + slug + "/"
        schema = {
            "@context": "https://schema.org", "@type": "CollectionPage",
            "name": hub["title"], "url": canonical, "description": hub["description"],
            "breadcrumb": {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Catalog", "item": SITE + "/catalog"},
                {"@type": "ListItem", "position": 3, "name": hub["category"]}]},
            "mainEntity": {"@type": "ItemList", "numberOfItems": len(chosen),
                "itemListElement": [
                    {"@type": "ListItem", "position": i + 1,
                     "name": p["display_title"], "url": SITE + p["url"]}
                    for i, p in enumerate(chosen)]}
        }
        sections = "\n".join(
            "<section><h2>" + esc(section["heading"]) + "</h2>" +
            "".join("<p>" + esc(para) + "</p>" for para in section["paragraphs"]) +
            "</section>" for section in hub["sections"]
        )
        cards = "\n".join(
            '<a class="product-card" href="' + esc(p["url"]) + '">' +
            ('<img class="category-thumb" src="' + esc(p["images"][0]) +
             '" alt="' + esc(p["display_title"]) +
             '" loading="lazy" decoding="async" width="360" height="225">' if p["images"] else '') +
            '<strong>' + esc(p["display_title"]) + '</strong><span>
        links = " ".join(
            '<a href="/catalog?category=' + esc(quote(other["category"], safe="")) + '">' +
            esc(other["category"]) + '</a>' for other in hubs if other["slug"] != slug
        )
        tokens = {
            "TITLE": esc(hub["seo_title"] + " | Digital Racer"),
            "DESCRIPTION": esc(hub["description"]),
            "CANONICAL": esc(canonical), "SCHEMA": json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
            "CATEGORY": esc(hub["category"]), "HEADING": esc(hub["title"]),
            "INTRO": esc(hub["intro"]), "SECTIONS": sections, "CARDS": cards,
            "COUNT": str(len(matches)), "DIRECTORY": directory, "HUBLINKS": links,
            "QUERY": esc(quote(hub["category"], safe=""))
        }
        page = template
        for key, value in tokens.items():
            page = page.replace("%%" + key + "%%", value)
        if "%%" in page:
            raise ValueError(f"Unresolved shop token: {slug}")
        write("shop/" + slug + "/index.html", page)
        slugs.append(slug)
    return slugs
 +
            esc(p["price"]) + ' USD</span></a>' for p in chosen
        )
        links = " ".join(
            '<a href="/catalog?category=' + esc(quote(other["category"], safe="")) + '">' +
            esc(other["category"]) + '</a>' for other in hubs if other["slug"] != slug
        )
        tokens = {
            "TITLE": esc(hub["seo_title"] + " | Digital Racer"),
            "DESCRIPTION": esc(hub["description"]),
            "CANONICAL": esc(canonical), "SCHEMA": json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
            "CATEGORY": esc(hub["category"]), "HEADING": esc(hub["title"]),
            "INTRO": esc(hub["intro"]), "SECTIONS": sections, "CARDS": cards,
            "COUNT": str(len(matches)), "DIRECTORY": directory, "HUBLINKS": links,
            "QUERY": esc(quote(hub["category"], safe=""))
        }
        page = template
        for key, value in tokens.items():
            page = page.replace("%%" + key + "%%", value)
        if "%%" in page:
            raise ValueError(f"Unresolved shop token: {slug}")
        write("shop/" + slug + "/index.html", page)
        slugs.append(slug)
    return slugs
