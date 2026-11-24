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

# Real listing-title matches only; no doorway pages or invented inventory.
FEATURE_GROUPS = {
    "pubg-mobile-accounts": [
        ("glacier-m416", "Glacier M416 accounts",
         "Compare the listed M416 Glacier weapon stage and Gun Lab details on each account page.",
         lambda t: "m416" in t and "glacier" in t),
        ("x-suits", "X-Suit collections",
         "Compare named X-Suits, their stated stages and other listed items.",
         lambda t: "xsuit" in t.replace("-", "").replace(" ", "")),
        ("conqueror", "Conqueror account collections",
         "Compare historic Conqueror achievements alongside the listed inventory.",
         lambda t: "conqueror" in t),
        ("mummy-sets", "Mummy outfit collections",
         "Check the named Mummy outfit and accompanying items in each listing.",
         lambda t: "mummy" in t),
    ],
    "pubg-mobile-car-cards": [
        ("bentley-bentayga", "Bentley Bentayga Azure cards",
         "Browse Bentayga vehicle finishes and confirm the exact car card before ordering.",
         lambda t: "bentayga" in t),
        ("bentley-continental", "Bentley Continental GTC Mulliner cards",
         "Compare the stated GTC and Continental finishes and listed prices.",
         lambda t: "gtc" in t or "continental" in t),
        ("bentley-flying-spur", "Bentley Flying Spur cards",
         "Inspect the named Flying Spur finishes, screenshots and details.",
         lambda t: "flying spur" in t),
    ],
    "pubg-mobile-in-game-items": [
        ("karambit-cards", "Karambit skin and gift cards",
         "Compare exact Karambit card names, listed prices and transfer requirements.",
         lambda t: "karambit" in t),
        ("sixtino-seventino", "Sixtino Seventino cards",
         "Compare Sixtino Seventino offers and verify the exact quantity and gifting terms.",
         lambda t: "sixtino" in t and "seventino" in t),
        ("taurino-assassino", "Taurino Assassino collectibles",
         "Explore Taurino Assassino variants and inspect the listed rarity or upgrade level.",
         lambda t: "taurino" in t and ("assassino" in t or "assasino" in t)),
    ],
}

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
    image_map_path = root / "assets" / "image-map.json"
    image_map = json.loads(image_map_path.read_text(encoding="utf-8")) if image_map_path.is_file() else {}
    slugs = []
    for hub in hubs:
        slug = hub["slug"]
        matches = [p for p in products if p["category"] == hub["category"]]
        chosen = list(reversed(matches))[:12]
        # During the Bentley event, ensure the Car Card hub always gives the
        # 12 featured slots to real Bentley listings, even after new imports
        # append unrelated Ferrari/Lamborghini/Porsche products.
        if slug == "pubg-mobile-car-cards":
            bentley = [p for p in reversed(matches)
                       if "bentley" in p["display_title"].casefold()]
            if bentley:
                chosen = bentley[:12]
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
            ('<img class="category-thumb" src="' + esc(image_map.get(p["images"][0], {}).get("480", p["images"][0])) +
             '" alt="' + esc(p["display_title"]) +
             '" loading="lazy" decoding="async" width="360" height="225">' if p["images"] else '') +
            '<strong>' + esc(p["display_title"]) + '</strong><span>$' +
            esc(p["price"]) + ' USD</span></a>' for p in chosen
        )
        features = ""
        if slug in FEATURE_GROUPS:
            groups = []
            for feature_id, name, advice, title_matches in FEATURE_GROUPS[slug]:
                found = [p for p in reversed(matches)
                         if title_matches(p["display_title"].casefold())]
                if not found:
                    continue
                items = "".join(
                    '<li><a href="' + esc(p["url"]) + '">' +
                    esc(p["display_title"]) + '</a><span>$' + esc(p["price"]) +
                    ' USD</span></li>' for p in found[:4]
                )
                groups.append(
                    '<section class="dr-feature-card" id="' + feature_id + '">'
                    '<h3>' + esc(name) + '</h3><p>' + esc(advice) + '</p>'
                    '<p class="dr-feature-count">' + str(len(found)) +
                    ' matching catalog titles</p><ul>' + items + '</ul></section>'
                )
            if groups:
                features = (
                    '<section class="dr-feature-groups" aria-labelledby="dr-feature-title">'
                    '<h2 id="dr-feature-title">Browse by named PUBG Mobile collectible</h2>'
                    '<p>These links lead to product pages whose listing titles mention '
                    'the named feature. Check screenshots, levels, price and current availability '
                    'before ordering.</p><div class="dr-feature-grid">' +
                    "".join(groups) + '</div></section>'
                )
        # The canonical category hubs are independently indexable; a filter
        # query on /catalog is not a distinct indexable category landing page.
        links = " ".join(
            '<a href="/shop/' + esc(other["slug"]) + '/">' +
            esc(other["title"]) + '</a>' for other in hubs if other["slug"] != slug
        )
        tokens = {
            "TITLE": esc(hub["seo_title"] + " | Digital Racer"),
            "DESCRIPTION": esc(hub["description"]),
            "CANONICAL": esc(canonical), "SCHEMA": json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
            "CATEGORY": esc(hub["category"]), "HEADING": esc(hub["title"]),
            "INTRO": esc(hub["intro"]), "SECTIONS": sections, "CARDS": cards,
            "FEATURES": features,
            "COUNT": str(len(matches)), "DIRECTORY": directory, "HUBLINKS": links,
            "QUERY": esc(quote(hub["category"], safe="")),
            "WHATSAPP_URL": esc("https://wa.me/923454342911?text=" + quote(
                ("Hello Digital Racer. I am interested in a PUBG Mobile Bentley 4.7 car-skin card from " +
                 canonical + ". Please confirm the exact Bentley model, finish, USD price, region and gifting eligibility.")
                if slug == "pubg-mobile-car-cards" else
                ("Hello Digital Racer. I want to buy " + hub["category"] +
                 " products from " + canonical +
                 ". Please confirm available listings, the USD price and delivery."), safe=""))
        }
        page = template
        for key, value in tokens.items():
            page = page.replace("%%" + key + "%%", value)
        if "%%" in page:
            raise ValueError(f"Unresolved shop token: {slug}")
        # Use the current real Car Card product photo for social link previews.
        # The preview updates automatically when catalog items change.
        if slug == "pubg-mobile-car-cards" and chosen[0]["images"]:
            raw_image = chosen[0]["images"][0]
            social_image = image_map.get(raw_image, {}).get("960", raw_image)
            social_url = social_image if social_image.startswith("https://") else SITE + social_image
            social_meta = ('<meta property="og:image" content="' + esc(social_url) + '">\n'
                           '<meta name="twitter:card" content="summary_large_image">\n'
                           '<meta name="twitter:image" content="' + esc(social_url) + '">\n')
            page = page.replace('<meta name="theme-color"', social_meta + '<meta name="theme-color"', 1)
        # Direct links to real Bentley models with demonstrated buyer search interest.
        # Keep titles and prices inventory-backed; removed listings disappear on rebuild.
        if slug == "pubg-mobile-car-cards":
            preferred_urls = (
                "/p/pubg-mobile-v4-7-bentley-car-card-flying-spur-nebula-showcase/",
                "/p/pubg-mobile-v4-7-bentley-car-card-batur-holoprism-collection/",
                "/p/pubg-mobile-v4-7-bentley-car-card-black-gold-luxury-showcase/",
                "/p/pubg-mobile-bentley-2026-car-card-for-sale-model-selection/",
                "/p/pubg-mobile-v4-7-bentley-car-skin-card-flying-spur-luxury-sedan/",
                "/p/bentley-prismatic-suv-car-card-pubg-mobile-bentayga-azure/",
            )
            by_url = {p["url"]: p for p in matches}
            fast_cards = []
            for target in preferred_urls:
                entry = by_url.get(target)
                if not entry:
                    continue
                message = ("Hello Digital Racer. I am interested in " + entry["display_title"] +
                           " (" + SITE + entry["url"] + ") listed at $" + str(entry["price"]) +
                           " USD. Please confirm the model, finish, region eligibility and final price.")
                chat = "https://wa.me/923454342911?text=" + quote(message, safe="")
                fast_cards.append(
                    '<article class="dr-bentley-fast-card"><a class="dr-bentley-fast-title" href="' +
                    esc(entry["url"]) + '">' + esc(entry["display_title"]) +
                    '</a><div class="dr-bentley-fast-details"><span>
        slugs.append(slug)
    return slugs
 + esc(entry["price"]) +
                    ' USD</span><a href="' + esc(chat) +
                    '" target="_blank" rel="noopener noreferrer">Ask on WhatsApp</a></div></article>'
                )
            if fast_cards:
                fast_section = (
                    '<section class="dr-bentley-fast" aria-labelledby="dr-bentley-fast-heading">'
                    '<h2 id="dr-bentley-fast-heading">Explore Bentley 4.7 car cards by model</h2>'
                    '<p>Compare exact vehicle finishes and USD listing prices, or ask about a specific '
                    'card directly on WhatsApp. Confirm gifting and regional eligibility before paying.</p>'
                    '<div class="dr-bentley-fast-grid">' + "".join(fast_cards) +
                    '</div></section>'
                )
                page = page.replace('<section class="listing-head">',
                                    fast_section + '<section class="listing-head">', 1)
                page = page.replace('</style>', ".dr-bentley-fast{margin:24px 0 14px;padding:17px;border:1px solid #65512d;border-radius:11px;background:#12100c}.dr-bentley-fast h2{margin:0 0 7px;font-size:1.19rem}.dr-bentley-fast>p{font-size:.9rem;margin-bottom:12px}.dr-bentley-fast-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.dr-bentley-fast-card{display:flex;flex-direction:column;justify-content:space-between;gap:9px;min-width:0;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:13px}.dr-bentley-fast-title{color:#f0d797;text-decoration:underline;text-underline-offset:3px;font-weight:700;font-size:.88rem;line-height:1.4;overflow-wrap:anywhere}.dr-bentley-fast-details{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap}.dr-bentley-fast-details span{font-size:.9rem;color:var(--gold);font-weight:750}.dr-bentley-fast-details a{display:inline-flex;min-height:42px;align-items:center;justify-content:center;border-radius:5px;background:#166a43;color:#fff;text-decoration:none;font-size:.83rem;font-weight:750;padding:7px 10px}.dr-bentley-fast-details a:hover,.dr-bentley-fast-details a:focus-visible{background:#228b57;color:#fff;outline:2px solid var(--gold);outline-offset:2px}@media(max-width:800px){.dr-bentley-fast-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.dr-bentley-fast{padding:12px;margin:16px 0 10px}.dr-bentley-fast-card{padding:11px}}@media(max-width:370px){.dr-bentley-fast-grid{grid-template-columns:1fr}}" + '</style>', 1)
        write("shop/" + slug + "/index.html", page)
        slugs.append(slug)
    return slugs
