#!/usr/bin/env python3
"""
Digital Racer SEO build script (Python 3 standard library only).

Run from anywhere after inventory.json changes:

    python3 scripts/build_seo.py

It reads inventory.json and (re)writes:
  * p/<slug>/index.html  - one pre-rendered page per product (copied from product.html,
                           so it keeps the exact same look and JavaScript)
  * p/index.json         - title/price -> clean URL map used by the site's JavaScript
  * the <!-- SEO:HEAD --> block in index.html, catalog.html and product.html
  * the <!-- SEO:GRID --> pre-rendered product cards in index.html and catalog.html
  * sitemap.xml and robots.txt

The output is deterministic: running it twice without changing inventory.json produces
no diff. Everything inside p/ is owned by this script and is deleted and rebuilt on
every run. Use `--check` to exit non-zero if any file would change (handy in CI).
"""
import html
import json
import os
import re
import shutil
import sys
import unicodedata
from urllib.parse import quote, urlsplit

# ---------------------------------------------------------------- site settings
SITE_URL = "https://www.digitalracer.store"  # canonical host (no trailing slash)
SITE_NAME = "Digital Racer"
WHATSAPP = "923454342911"
HOME_TITLE = "Digital Racer — PUBG Mobile Accounts, Car Cards, UC, Items & Rank Boosting"
HOME_DESC = ("Browse PUBG Mobile accounts, car cards, UC top-ups, in-game items and "
             "rank boosting. See USD prices and product photos. Buy directly on WhatsApp.")
CATALOG_TITLE = "Full Catalog — PUBG Mobile Accounts, Car Cards, UC, Items & Boosting | Digital Racer"
CATALOG_DESC = ("Browse every PUBG Mobile account, car skin card, UC top-up, in-game item and rank boosting "
                "service listed at Digital Racer. "
                "View USD prices and order directly on WhatsApp.")
LOGO_PATH = "/images/icons/icon-512.png"
CATEGORY_LABELS = {"Account": "PUBG Mobile Account", "Car Card": "PUBG Mobile Car Skin Card",
                   "UC Top-Up": "PUBG Mobile UC Top-Up", "In-Game Items": "PUBG Mobile In-Game Item",
                   "Rank Boosting": "PUBG Mobile Rank Boosting Service"}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = "p"  # pre-rendered product pages live at /p/<slug>/

CHECK_ONLY = "--check" in sys.argv
changed = []


# ---------------------------------------------------------------- helpers
def path(*parts):
    return os.path.join(ROOT, *parts)


def read(rel):
    with open(path(rel), encoding="utf-8") as f:
        return f.read()


ADSENSE_SCRIPT = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3636750354534911" crossorigin="anonymous"></script>'
ADSENSE_AUTHORIZATION = "google.com, pub-3636750354534911, DIRECT, f08c47fec0942fa0\n"


def with_adsense(content):
    """Keep exactly one publisher loader in every generated HTML head."""
    if ADSENSE_SCRIPT in content:
        return content
    if "<head>" not in content:
        raise ValueError("HTML page is missing its head")
    return content.replace("<head>", "<head>\n" + ADSENSE_SCRIPT, 1)


def write(rel, content):
    if rel.endswith(".html"):
        content = with_adsense(content)
    full = path(rel)
    old = None
    if os.path.exists(full):
        with open(full, encoding="utf-8") as f:
            old = f.read()
    if old == content:
        return
    changed.append(rel)
    if CHECK_ONLY:
        return
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def esc(s):
    return html.escape(str(s), quote=True)


def strip_symbols(s):
    """Drop emoji / decorative symbols and supplier separators, collapse whitespace."""
    out = []
    for ch in str(s):
        cat = unicodedata.category(ch)
        if cat in ("So", "Sk", "Cs", "Co", "Cn") or cat.startswith("C") and ch not in "\n\t":
            out.append(" ")
        elif ch in "\u200d\ufe0f\ufe0e":
            continue
        else:
            out.append(ch)
    s = "".join(out)
    s = s.replace("*", " ").replace('"', ", ").replace("\u2e31", " ")
    s = re.sub(r"\s*,\s*(,\s*)+", ", ", s)
    s = re.sub(r"\(\s*\)", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" ,|-")
    return s


def truncate(s, limit):
    if len(s) <= limit:
        return s
    cut = s[: limit - 1]
    if " " in cut[limit // 2:]:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,|-·") + "…"


def slugify(s):
    s = unicodedata.normalize("NFKD", strip_symbols(s)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    if len(s) > 70:
        s = s[:70]
        s = s[: s.rfind("-")] if "-" in s[35:] else s
    return s.strip("-") or "item"


def img_path(raw):
    """Mirror formatImagePath() in the site JS, and URL-encode it."""
    if not raw or not str(raw).strip():
        return ""
    p = str(raw).strip()
    if "\\" in p or p.startswith("//") or any(ord(c) < 32 for c in p):
        return ""
    if re.match(r"^[a-z][a-z0-9+.-]*:", p, re.I):
        u = urlsplit(p)
        return p if u.scheme == "https" and u.netloc and not u.username and not u.password else ""
    if not p.startswith("/"):
        p = "/" + p
    return quote(p, safe="/()@!$&'*+,;=:-._~")


def abs_url(p):
    return p if p.startswith("http") else SITE_URL + p


def fmt_price(price):
    try:
        return f"{float(str(price).replace('$', '').replace(',', '').strip()):.2f}"
    except ValueError:
        return None


def jsonld(obj):
    s = json.dumps(obj, ensure_ascii=False, indent=1)
    return '<script type="application/ld+json">\n' + s.replace("</", "<\\/") + "\n</script>"


def replace_block(text, begin, end, content, fname):
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end), re.S)
    matches = pattern.findall(text)
    if len(matches) != 1:
        sys.exit(f"build_seo: expected exactly one '{begin}' ... '{end}' block in {fname}, found {len(matches)}")
    return pattern.sub(lambda m: begin + content + end, text)


def replace_one(text, regex, repl, fname, what):
    new, n = re.subn(regex, repl, text, count=1, flags=re.S)
    if n != 1:
        sys.exit(f"build_seo: could not find {what} in {fname} (product.html markup changed?)")
    return new


def parse_description(text):
    """Python port of parseDescription() in product.html (with HTML escaping)."""
    out, in_list = [], False
    for line in (text or "").split("\n"):
        t = line.strip()
        if t.startswith("-"):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{esc(t[1:].strip())}</li>")
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
            if t:
                out.append(f"<p>{esc(t)}</p>")
    if in_list:
        out.append("</ul>")
    return "".join(out)


# ---------------------------------------------------------------- data
data = json.loads(read("inventory.json"))
items = data if isinstance(data, list) else (data.get("items") or data.get("products") or data.get("inventory") or [])

products, used = [], set()
for it in items:
    title = str(it.get("title") or "").strip()
    if not title:
        continue
    slug = slugify(title)
    if slug in used:
        price_slug = re.sub(r"[^0-9]+", "-", str(it.get("price", ""))).strip("-")
        slug = f"{slug}-{price_slug}" if price_slug else slug
        n = 2
        base = slug
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
    used.add(slug)
    images = []
    for raw in [it.get("thumbnail") or it.get("image") or it.get("img") or ""] + list(it.get("gallery") or []):
        p = img_path(raw)
        if p and p != "/" and p not in images:
            images.append(p)
    category = it.get("category") or "Product"
    desc_raw = it.get("description") or ""
    clean_title = strip_symbols(title)
    products.append({
        "raw": it,
        "title": title,
        "clean_title": clean_title,
        "slug": slug,
        "url": f"/{OUT_DIR}/{slug}/",
        "price": it.get("price", ""),
        "price_num": fmt_price(it.get("price", "")),
        "category": category,
        "cat_label": CATEGORY_LABELS.get(category, f"PUBG Mobile {category}"),
        "images": images,
        "desc_raw": desc_raw,
        "desc_clean": strip_symbols(desc_raw),
    })


IMAGE_MAP = json.loads(read("assets/image-map.json")) if os.path.exists(path("assets/image-map.json")) else {}

def display_image(image, size=480):
    return IMAGE_MAP.get(image, {}).get(str(size), image)

def card_html(p, indent, eager=False):
    """Same markup as createCardHTML() in index.html / catalog.html."""
    img = display_image(p["images"][0]) if p["images"] else ""
    badge = f'<div class="prod-badge">{esc(p["raw"].get("badge"))}</div>' if p["raw"].get("badge") else ""
    extra = f' item-card" data-category="{esc(p["category"])}' if indent == "catalog" else ""
    return (f'<a href="{p["url"]}" class="product-card{extra}">'
            f'<div class="prod-img-wrap"><img src="{esc(img)}" class="prod-img" alt="{esc(p["clean_title"])}" {'fetchpriority="high"' if eager else 'loading="lazy"'} decoding="async" onerror="this.style.display=\'none\'"> {badge}</div>'
            f'<div class="prod-content"><div class="prod-category">{esc(p["category"])}</div>'
            f'<div class="prod-title">{esc(p["title"])}</div>'
            f'<div class="prod-footer"><div class="prod-price">${esc(p["price"])} USD</div><div class="prod-btn">View</div></div></div></a>')


def head_tags(title, desc, canonical, image=None, og_type="website", extra_meta="", ld=()):
    lines = [
        f"<title>{esc(title)}</title>",
        f'<meta name="description" content="{esc(desc)}">',
    ]
    if canonical:
        lines.append(f'<link rel="canonical" href="{esc(canonical)}">')
    lines += [
        '<meta name="theme-color" content="#050505">',
        '<link rel="icon" href="/favicon.ico" sizes="32x32">',
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
        '<link rel="apple-touch-icon" href="/images/icons/apple-touch-icon.png">',
        f'<meta property="og:site_name" content="{SITE_NAME}">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
    ]
    if canonical:
        lines.append(f'<meta property="og:url" content="{esc(canonical)}">')
    if image:
        lines.append(f'<meta property="og:image" content="{esc(abs_url(image))}">')
    lines += [
        f'<meta name="twitter:card" content="{"summary_large_image" if image else "summary"}">',
        f'<meta name="twitter:title" content="{esc(title)}">',
        f'<meta name="twitter:description" content="{esc(desc)}">',
    ]
    if image:
        lines.append(f'<meta name="twitter:image" content="{esc(abs_url(image))}">')
    if extra_meta:
        lines.append(extra_meta)
    lines += [jsonld(x) for x in ld]
    return "\n" + "\n".join(lines) + "\n"


ORG = {
    "@type": "Organization",
    "@id": SITE_URL + "/#organization",
    "name": SITE_NAME,
    "sameAs": ["https://www.facebook.com/digitalracerstore"],
    "url": SITE_URL + "/",
    "logo": SITE_URL + LOGO_PATH,
    "contactPoint": {"@type": "ContactPoint", "telephone": "+" + WHATSAPP,
                     "contactType": "customer service", "availableLanguage": ["English"]},
}
WEBSITE = {"@type": "WebSite", "@id": SITE_URL + "/#website", "name": SITE_NAME,
           "url": SITE_URL + "/", "publisher": {"@id": SITE_URL + "/#organization"}}
default_image = next((p["images"][0] for p in products if p["images"]), None)


def crumbs(*pairs):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, **({"item": u} if u else {})}
        for i, (n, u) in enumerate(pairs)]}


# ---------------------------------------------------------------- index.html
def cat_filter(key):
    def f(p):
        c = (p["category"] or "").lower()
        if key == "accounts":
            return "account" in c
        if key == "skins":
            return "car" in c or "skin" in c or "card" in c
        if key == "items":
            return "item" in c
        if key == "boosting":
            return "boost" in c or "rank" in c
        return "uc" in c
    return f


s = read("index.html")
s = replace_block(s, "<!-- SEO:HEAD:BEGIN (generated by scripts/build_seo.py; do not edit by hand) -->",
                  "<!-- SEO:HEAD:END -->",
                  head_tags(HOME_TITLE, HOME_DESC, SITE_URL + "/", default_image,
                            ld=[{"@context": "https://schema.org", "@graph": [ORG, WEBSITE]}]), "index.html")
for key, label in [("accounts", "Account"), ("skins", "Skin"), ("uc", "UC Pack"),
                   ("items", "In-Game Item"), ("boosting", "Rank Boosting Service")]:
    sel = [p for p in products if cat_filter(key)(p)][-4:][::-1]  # newest first (new items are appended)
    inner = ("\n      " + "\n      ".join(card_html(p, "home", eager=(key == "accounts" and i < 2)) for i, p in enumerate(sel)) + "\n      ") if sel else \
        f'\n      <p style="color: var(--muted);">No {label}s available right now.</p>\n      '
    s = replace_block(s, f"<!-- SEO:GRID:{key}:BEGIN -->", f"<!-- SEO:GRID:{key}:END -->", inner, "index.html")
write("index.html", s)

# ---------------------------------------------------------------- catalog.html
catalog_products = list(reversed(products))  # Match the catalog's default newest-first order.
item_list = {"@context": "https://schema.org", "@type": "ItemList", "name": "Digital Racer catalog",
             "numberOfItems": len(products),
             "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": SITE_URL + p["url"],
                                  "name": p["clean_title"]} for i, p in enumerate(catalog_products)]}
s = read("catalog.html")
s = replace_block(s, "<!-- SEO:HEAD:BEGIN (generated by scripts/build_seo.py; do not edit by hand) -->",
                  "<!-- SEO:HEAD:END -->",
                  head_tags(CATALOG_TITLE, CATALOG_DESC, SITE_URL + "/catalog", default_image,
                            ld=[crumbs(("Home", SITE_URL + "/"), ("Catalog", None)), item_list]), "catalog.html")
inner = ("\n    " + "\n    ".join(card_html(p, "catalog", eager=i < 2) for i, p in enumerate(catalog_products)) + "\n    ") if products else \
    '\n    <p style="color: var(--muted);">No products found matching your search.</p>\n    '
s = replace_block(s, "<!-- SEO:GRID:catalog:BEGIN -->", "<!-- SEO:GRID:catalog:END -->", inner, "catalog.html")
s = re.sub(r'(<p id="catalog-count"[^>]*>).*?(</p>)',
           lambda m: m.group(1) + f"{len(products)} products" + m.group(2), s)
write("catalog.html", s)

# ---------------------------------------------------------------- product.html (generic, ?item= links)
template = read("product.html")
generic = replace_block(template, "<!-- SEO:HEAD:BEGIN (generated by scripts/build_seo.py; do not edit by hand) -->",
                        "<!-- SEO:HEAD:END -->",
                        head_tags("Product Details | Digital Racer",
                                  "Browse PUBG Mobile product details, photos and USD prices. Order directly from Digital Racer on WhatsApp.",
                                  None, default_image, extra_meta='<meta name="robots" content="noindex, follow">'), "product.html")
write("product.html", generic)
template = generic

# ---------------------------------------------------------------- product pages
def product_page(p, others):
    it = p["raw"]
    short = truncate(p["clean_title"], 60)
    if sum(1 for o in products if o["clean_title"] == p["clean_title"]) > 1:
        short = f"{truncate(p['clean_title'], 42)} · Listing {1 + [o for o in products if o['clean_title'] == p['clean_title']].index(p)} (${p['price']})"  # keep duplicate titles distinct
    page_title = f"{short} | {SITE_NAME}" if "pubg" in p["clean_title"].lower() else f"{short} – {p['cat_label']} | {SITE_NAME}"
    price_txt = f"${p['price']} USD"
    delivery = "Order on WhatsApp"
    lead = f"{p['cat_label']} · {price_txt} · {delivery}. "
    meta_desc = truncate(lead + (p["desc_clean"] or p["clean_title"]), 158)
    canonical = SITE_URL + p["url"]
    image = p["images"][0] if p["images"] else None

    offer = {"@type": "Offer", "url": canonical, "priceCurrency": "USD",
             "availability": "https://schema.org/InStock", "seller": {"@id": SITE_URL + "/#organization"}}
    if p["price_num"]:
        offer["price"] = p["price_num"]
    product_ld = {"@context": "https://schema.org", "@type": "Product", "@id": canonical + "#product",
                  "name": truncate(p["clean_title"], 150), "sku": p["slug"], "category": p["cat_label"],
                  "description": truncate(p["desc_clean"] or p["clean_title"], 4900),
                  "image": [abs_url(i) for i in p["images"]], "url": canonical, "offers": offer}
    if not product_ld["image"]:
        del product_ld["image"]
    org_ld = {"@context": "https://schema.org", **ORG}
    bc = crumbs(("Home", SITE_URL + "/"), ("Catalog", SITE_URL + "/catalog"),
                (p["category"], SITE_URL + "/catalog?category=" + quote(p["category"])), (short, None))
    extra = ""
    if p["price_num"]:
        extra = (f'<meta property="product:price:amount" content="{p["price_num"]}">\n'
                 f'<meta property="product:price:currency" content="USD">')
    s = replace_block(template, "<!-- SEO:HEAD:BEGIN (generated by scripts/build_seo.py; do not edit by hand) -->",
                      "<!-- SEO:HEAD:END -->",
                      head_tags(page_title, meta_desc, canonical, image, "product", extra,
                                [product_ld, bc, org_ld]), p["url"])
    f = p["url"]
    # --- body: same elements the page's JavaScript fills in, so it looks identical before/after JS
    s = replace_one(s, r'(<a href="/catalog" id="bread-cat">).*?(</a>)',
                    lambda m: f'<a href="/catalog?category={esc(quote(p["category"]))}" id="bread-cat">{esc(p["category"])}</a>', f, "breadcrumb")
    s = replace_one(s, r'(<h1 class="main-title" id="prod-title">).*?(</h1>)',
                    lambda m: m.group(1) + esc(p["title"]) + m.group(2), f, "title h1")
    s = replace_one(s, r'(<div class="buy-price" id="prod-price">).*?(</div>)',
                    lambda m: m.group(1) + esc(price_txt) + m.group(2), f, "price")
    s = replace_one(s, r'(<span id="prod-tag">).*?(</span>)',
                    lambda m: m.group(1) + esc(it.get("tag") or "GLOBAL") + m.group(2), f, "tag")
    specs = ""
    if it.get("account_level"):
        specs += f'\n          <div class="mini-spec" data-extra><span>Account Level</span><span>{esc(it["account_level"])}</span></div>'
    if it.get("highest_tier"):
        specs += f'\n          <div class="mini-spec" data-extra><span>Highest Tier</span><span>{esc(it["highest_tier"])}</span></div>'
    s = replace_one(s, r'(<div class="mini-spec"><span>Delivery</span><span style="color: var\(--accent\);">Instant</span></div>)',
                    lambda m: m.group(1) + specs, f, "specs grid")
    desc_prefix = "<p><strong>Buy now on whatsapp number +923454342911</strong></p><br>"
    desc_html = desc_prefix + parse_description(p["desc_raw"])
    s = replace_one(s, r'(<div class="desc-content" id="prod-desc">)(</div>)',
                    lambda m: m.group(1) + desc_html + m.group(2), f, "description")
    if image:
        multi = len(p["images"]) > 1
        disp = "block" if multi else "none"
        s = replace_one(s, r'<div class="main-nav-btn main-prev" id="main-prev"', f'<div class="main-nav-btn main-prev" id="main-prev" style="display: {disp};"', f, "prev btn")
        s = replace_one(s, r'<div class="main-nav-btn main-next" id="main-next"', f'<div class="main-nav-btn main-next" id="main-next" style="display: {disp};"', f, "next btn")
        s = replace_one(s, r'<img src="" alt="" id="main-display-img"[^>]*>',
                        lambda m: f'<img src="{esc(display_image(image, 960))}" alt="{esc(p["clean_title"])}" role="button" tabindex="0" aria-label="Enlarge product image" onkeydown="if(event.key===&quot;Enter&quot;||event.key===&quot; &quot;){{event.preventDefault();this.click()}}" id="main-display-img" data-index="0" fetchpriority="high" onclick="openLightbox(this.getAttribute(\'data-index\'))" style="display: block;">', f, "main image")
        if multi:
            thumbs = "".join(f'<img src="{esc(display_image(im))}" alt="Product image {i + 1}" role="button" tabindex="0" aria-label="Show product image {i + 1}" onkeydown="if(event.key===&quot;Enter&quot;||event.key===&quot; &quot;){{event.preventDefault();this.click()}}" class="gal-thumb {"active" if i == 0 else ""}" loading="lazy" decoding="async" onclick="changeMainImage({i})">'
                             for i, im in enumerate(p["images"]))
            s = replace_one(s, r'(<div id="gallery-container" class="gallery-wrap">)(</div>)', lambda m: m.group(1) + thumbs + m.group(2), f, "gallery")
        else:
            s = replace_one(s, r'<div id="gallery-container" class="gallery-wrap"></div>', '<div id="gallery-container" class="gallery-wrap" style="display: none;"></div>', f, "gallery")
    msg = f"Hello Digital Racer! I want to acquire: {p['title']} for ${p['price']} USD."
    s = replace_one(s, r'<a href="#" class="whatsapp-btn" id="buy-btn">',
                    lambda m: f'<a href="https://wa.me/{WHATSAPP}?text={esc(quote(msg, safe=""))}" class="whatsapp-btn" id="buy-btn">', f, "buy button")
    rel = "".join(
        f'<a href="{o["url"]}" class="rel-card"><img src="{esc(display_image(o["images"][0])) if o["images"] else ""}" class="rel-img" alt="{esc(o["clean_title"])}" loading="lazy" onerror="this.style.display=\'none\'">'
        f'<div class="rel-content"><div class="rel-title">{esc(o["title"])}</div><div class="rel-price">${esc(o["price"])} USD</div></div></a>'
        for o in others) or '<p style="color: var(--muted);">No other products available.</p>'
    s = replace_one(s, r'(<div class="related-grid" id="related-grid">).*?(</div>\n</div>)',
                    lambda m: m.group(1) + rel + m.group(2), f, "related grid")
    preset = json.dumps({"title": p["title"], "price": p["price"], "thumbnail": it.get("thumbnail")}, ensure_ascii=False).replace("</", "<\\/")
    s = replace_one(s, r'\n<script>\n  const urlParams', lambda m: f"\n<script>window.DR_PRESET = {preset};</script>" + m.group(0), f, "main script")
    if it.get("supplier_listing_id"):
        s = s.replace("\n        Instant Delivery\n", "\n        Digital Delivery\n")
        s = s.replace("Verified Account", "Account Details" if "account" in p["category"].lower() else "Item Details")
        s = s.replace('>Instant</span>', '>Digital delivery</span>')
        s = s.replace('<span>SECURE GUARANTEE:</span> All transactions and asset transfers are verified and protected for smooth delivery.',
                      '<span>ORDER DETAILS:</span> Order directly from Digital Racer using Buy Now.')
    return s


expected = set()
for p in products:
    others = sorted([o for o in products if o is not p], key=lambda o: o["category"] != p["category"])[:4]  # same choice as the page's JavaScript
    rel = f"{OUT_DIR}/{p['slug']}/index.html"
    expected.add(rel)
    write(rel, product_page(p, others))

manifest = [{"title": p["title"], "price": p["price"], "thumbnail": p["raw"].get("thumbnail"), "url": p["url"]} for p in products]
expected.add(f"{OUT_DIR}/index.json")
write(f"{OUT_DIR}/index.json", json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")

# ---------------------------------------------------------------- old URLs of renamed products
# scripts/redirects.json maps an old product slug to its current slug: {"old-slug": "new-slug"}.
# For each entry we keep /p/<old-slug>/ alive as a tiny redirect page (canonical + meta refresh)
# and add a real 301 rule to /_redirects (Cloudflare static assets), so URLs Google already knows keep working.
redirects = {}
if os.path.exists(path("scripts", "redirects.json")):
    with open(path("scripts", "redirects.json"), encoding="utf-8") as f:
        redirects = json.load(f)
live_slugs = {p["slug"]: p for p in products}
rules = []
for old, new in sorted(redirects.items()):
    while new in redirects and new not in live_slugs:  # follow chains of renames
        new = redirects[new]
    if old in live_slugs or new not in live_slugs:
        print(f"build_seo: skipping redirect {old} -> {new} (old slug is live or target missing)")
        continue
    target = f"/{OUT_DIR}/{new}/"
    tp = live_slugs[new]
    page = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
            f'<title>{esc(truncate(tp["clean_title"], 60))} | {SITE_NAME}</title>\n'
            f'<link rel="canonical" href="{esc(SITE_URL + target)}">\n'
            f'<meta http-equiv="refresh" content="0; url={esc(target)}">\n'
            '<meta name="robots" content="noindex, follow">\n'
            f'<script>location.replace({json.dumps(target)});</script>\n</head>\n<body>\n'
            f'<p>This product has moved: <a href="{esc(target)}">{esc(tp["clean_title"])}</a></p>\n</body>\n</html>\n')
    rel = f"{OUT_DIR}/{old}/index.html"
    expected.add(rel)
    write(rel, page)
    rules.append(f"/{OUT_DIR}/{old}/ {target} 301")
    rules.append(f"/{OUT_DIR}/{old} {target} 301")
if rules or os.path.exists(path("_redirects")):
    write("_redirects", "# generated by scripts/build_seo.py from scripts/redirects.json; do not edit by hand\n"
          + "\n".join(rules) + "\n")

# remove pages for products that no longer exist
if os.path.isdir(path(OUT_DIR)):
    for dirpath, _, files in os.walk(path(OUT_DIR)):
        for fn in files:
            rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace(os.sep, "/")
            if rel not in expected:
                changed.append(rel + " (deleted)")
                if not CHECK_ONLY:
                    os.remove(os.path.join(dirpath, fn))
    if not CHECK_ONLY:
        for dirpath, dirs, files in sorted(os.walk(path(OUT_DIR)), reverse=True):
            if not os.listdir(dirpath):
                os.rmdir(dirpath)

# ---------------------------------------------------------------- sitemap.xml + robots.txt
x = ['<?xml version="1.0" encoding="UTF-8"?>',
     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
x += [f"  <url><loc>{SITE_URL}/</loc></url>", f"  <url><loc>{SITE_URL}/catalog</loc></url>"]
x += [f"  <url><loc>{SITE_URL}/{page}/</loc></url>" for page in ("about", "contact", "terms", "privacy")]
for p in products:
    imgs = "".join(f"<image:image><image:loc>{esc(abs_url(i))}</image:loc></image:image>" for i in p["images"][:10])
    x.append(f"  <url><loc>{esc(SITE_URL + p['url'])}</loc>{imgs}</url>")
x.append("</urlset>")
write("sitemap.xml", "\n".join(x) + "\n")

write("robots.txt", "User-agent: *\nAllow: /\nDisallow: /admin/\n\nSitemap: " + SITE_URL + "/sitemap.xml\n")

# Keep standalone site heads and the publisher authorization in sync, too.
for rel in ("404.html", "admin/index.html", "about/index.html",
            "contact/index.html", "privacy/index.html", "terms/index.html"):
    write(rel, read(rel))
write("ads.txt", ADSENSE_AUTHORIZATION)

if CHECK_ONLY:
    if changed:
        print("build_seo: out of date:\n  " + "\n  ".join(changed))
        sys.exit(1)
    print("build_seo: up to date")
else:
    print(f"build_seo: {len(products)} products, {len(changed)} file(s) updated")
    for c in changed:
        print("  " + c)
