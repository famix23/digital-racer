#!/usr/bin/env python3
"""Build self-contained DigitalRacer blog pages from plain-text JSON.

The existing product/catalog generator calls this module. No external editorial links.
"""
from pathlib import Path
from datetime import date
import html
import json
import re

BASE = "https://www.digitalracer.store"
MARKER = "<!-- BLOG:GENERATED;"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_TOPICS = {"skins", "account-security", "emulator", "uc-safety", "events", "tutorial"}

def load_posts(root):
    root = Path(root)
    posts = []
    slugs = set()
    for file in sorted((root / "content" / "blog").glob("*.json")):
        item = json.loads(file.read_text(encoding="utf-8"))
        slug = item.get("slug", "")
        if not isinstance(slug, str) or not SLUG.fullmatch(slug) or slug in slugs:
            raise ValueError(f"Invalid/duplicate blog slug: {file}")
        slugs.add(slug)
        text = []
        for key in ("title", "summary", "category", "published", "intro"):
            value = item.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{file}: missing {key}")
            text.append(value)
        published = date.fromisoformat(item["published"])
        if "modified" in item:
            modified = item["modified"]
            if not isinstance(modified, str) or date.fromisoformat(modified) < published:
                raise ValueError(f"{file}: modified must be a date on/after published")
        topics = item.get("topics")
        if (not isinstance(topics, list) or
            any(not isinstance(t, str) or t not in ALLOWED_TOPICS for t in topics) or
            len(topics) != len(set(topics))):
            raise ValueError(f"{file}: topics must list distinct editorial topics")
        if not isinstance(item.get("sections"), list) or not item["sections"]:
            raise ValueError(f"{file}: sections required")
        for section in item["sections"]:
            heading = section.get("heading")
            paragraphs = section.get("paragraphs")
            points = section.get("points", [])
            if not isinstance(heading, str) or not heading.strip():
                raise ValueError(f"{file}: section heading required")
            if not isinstance(paragraphs, list) or not paragraphs or not all(isinstance(p, str) and p.strip() for p in paragraphs):
                raise ValueError(f"{file}: nonempty paragraph list required")
            if not isinstance(points, list) or not all(isinstance(p, str) and p.strip() for p in points):
                raise ValueError(f"{file}: invalid bullet list")
            text.extend([heading] + paragraphs + points)
        if len(" ".join(text).split()) < 450:
            raise ValueError(f"{file}: article is thin; needs more useful verified detail")
        if any("<" in t or ">" in t or re.search(r"https?://", t) for t in text):
            raise ValueError(f"{file}: plain text only; no HTML or outbound URLs")
        posts.append(item)
    return sorted(posts, key=lambda p: p["slug"])

def render(template, title, summary, category, canonical, body, is_article):
    values = {"TITLE": html.escape(title), "SUMMARY": html.escape(summary, quote=True),
              "CATEGORY": html.escape(category), "CANONICAL": html.escape(canonical, quote=True),
              "OG_TYPE": "article" if is_article else "website", "BODY": body}
    for key, val in values.items():
        template = template.replace("%%" + key + "%%", val)
    if "%%" in template:
        raise ValueError("Unresolved blog template token")
    return template

def article_context(page, post):
    """Add truthful publication and publisher metadata to an existing article page."""
    canonical = BASE + "/blog/" + post["slug"] + "/"
    schema = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post["title"],
        "description": post["summary"],
        "datePublished": post["published"],
        "author": {"@type": "Organization", "name": "Digital Racer",
                   "url": BASE + "/about/"},
        "publisher": {"@type": "Organization", "name": "Digital Racer",
                      "url": BASE + "/"},
        "mainEntityOfPage": canonical,
    }
    if "modified" in post:
        schema["dateModified"] = post["modified"]
    ld = '<script type="application/ld+json">' + json.dumps(
        schema, ensure_ascii=False, separators=(",", ":")
    ).replace("</", "<\\/") + '</script>\n'
    if page.count("</head>") != 1:
        raise ValueError("Expected one blog article head")
    page = page.replace("</head>", ld + "</head>", 1)
    published = date.fromisoformat(post["published"])
    display_date = f"{published:%B} {published.day}, {published.year}"
    h1 = "<h1>" + html.escape(post["title"]) + "</h1>"
    if page.count(h1) != 1:
        raise ValueError("Expected one blog article heading")
    byline = ('<p class="article-meta">Published <time datetime="' +
              html.escape(post["published"], quote=True) + '">' +
              html.escape(display_date) +
              '</time> · By <a href="/about/">Digital Racer</a></p>')
    if "modified" in post:
        modified = date.fromisoformat(post["modified"])
        updated_date = f"{modified:%B} {modified.day}, {modified.year}"
        byline = byline.replace(
            "</p>",
            ' · Updated <time datetime="' + html.escape(post["modified"], quote=True)
            + '">' + html.escape(updated_date) + "</time></p>", 1)
    return page.replace(h1, h1 + "\n" + byline, 1)


def article_body(post):
    parts = ['<p class="lede">' + html.escape(post["intro"]) + '</p>']
    for section in post["sections"]:
        parts.append("<h2>" + html.escape(section["heading"]) + "</h2>")
        for p in section["paragraphs"]:
            parts.append("<p>" + html.escape(p) + "</p>")
        if section.get("points"):
            parts.append("<ul>" + "".join("<li>" + html.escape(p) + "</li>" for p in section["points"]) + "</ul>")
    parts.append('<section class="more"><h2>Explore more on Digital Racer</h2><p><a href="/blog/">More gaming articles</a> · <a href="/guides/">Gaming guides</a> · <a href="/catalog">Gaming catalog</a></p></section>')
    return "\n".join(parts)

def build_blog(root, write, check_only=False, changed=None):
    root = Path(root)
    template = (root / "scripts" / "blog_template.html.txt").read_text(encoding="utf-8")
    posts = load_posts(root)
    def category_group(item):
        category = item["category"].lower()
        if category.startswith("pubg"):
            return "PUBG Mobile"
        if category.startswith("gta vi"):
            return "GTA VI"
        if category.startswith("gta v"):
            return "GTA V"
        return "Other Gaming & PCs"

    groups = (("PUBG Mobile", "pubg-mobile"), ("GTA VI", "gta-vi"),
              ("GTA V", "gta-v"), ("Other Gaming & PCs", "other-gaming"))
    hub_parts = [
        '<p class="lede">Original gaming news, update previews and practical guides for Digital Racer readers, with PUBG Mobile as our main coverage area.</p>',
        '<p>Browse <a href="#pubg-mobile">PUBG Mobile</a>, <a href="#gta-vi">GTA VI</a>, <a href="#gta-v">GTA V</a> or <a href="#other-gaming">other gaming and PC topics</a>.</p>'
    ]
    for name, anchor in groups:
        members = [p for p in posts if category_group(p) == name]
        cards = "\n".join(
            '<a href="/blog/' + p["slug"] + '/"><strong>' + html.escape(p["title"]) +
            '</strong><span>' + html.escape(p["summary"]) + '</span></a>'
            for p in members)
        hub_parts.append('<h2 id="' + anchor + '">' + html.escape(name) + '</h2>')
        hub_parts.append('<div class="cards">' + cards + '</div>')
    hub_parts.append('<p>News articles identify confirmed announcements and distinguish beta previews from final releases. Learn more about cosmetics and player safety in our <a href="/guides/">gaming guides</a>.</p>')
    hub = "\n".join(hub_parts)
    write("blog/index.html", render(template, "Gaming Blog", "Original gaming articles and practical PC gaming insights from Digital Racer.", "Gaming articles", BASE + "/blog/", hub, False))
    for p in posts:
        write("blog/" + p["slug"] + "/index.html",
              article_context(render(template, p["title"], p["summary"], p["category"],
                                     BASE + "/blog/" + p["slug"] + "/", article_body(p), True), p))
    expected = {p["slug"] for p in posts}
    for page in (root / "blog").glob("*/index.html"):
        if page.parent.name not in expected and MARKER in page.read_text(encoding="utf-8"):
            if changed is not None:
                changed.append(page.relative_to(root).as_posix() + " (deleted)")
            if not check_only:
                page.unlink()
    return [p["slug"] for p in posts]
