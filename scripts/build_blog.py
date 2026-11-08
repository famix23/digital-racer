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
        date.fromisoformat(item["published"])
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
    cards = "\n".join(
        '<a href="/blog/' + p["slug"] + '/"><strong>' + html.escape(p["title"]) +
        '</strong><span>' + html.escape(p["summary"]) + '</span></a>'
        for p in posts)
    hub = '<p class="lede">Gaming information, PC performance explainers and practical tutorials written for Digital Racer readers. Browse without visiting third-party websites.</p>\n<div class="cards">' + cards + '</div>\n<p>New topics can be added independently of the product catalog. Find PUBG Mobile item terminology in our <a href="/guides/">gaming guides</a>.</p>'
    write("blog/index.html", render(template, "Gaming Blog", "Original gaming articles and practical PC gaming insights from Digital Racer.", "Gaming articles", BASE + "/blog/", hub, False))
    for p in posts:
        write("blog/" + p["slug"] + "/index.html",
              render(template, p["title"], p["summary"], p["category"],
                     BASE + "/blog/" + p["slug"] + "/", article_body(p), True))
    expected = {p["slug"] for p in posts}
    for page in (root / "blog").glob("*/index.html"):
        if page.parent.name not in expected and MARKER in page.read_text(encoding="utf-8"):
            if changed is not None:
                changed.append(page.relative_to(root).as_posix() + " (deleted)")
            if not check_only:
                page.unlink()
    return [p["slug"] for p in posts]
