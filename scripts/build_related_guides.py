#!/usr/bin/env python3
"""Generate relevant, internal-only article recommendations for the four guide pages.

Article topic tags live in content/blog/*.json. This deliberately never modifies
inventory, catalog, product pages or the homepage's product-first layout.
"""
from pathlib import Path
import html
import re

START = "<!-- GUIDE:RELATED:BEGIN -->"
END = "<!-- GUIDE:RELATED:END -->"
TARGETS = (
    ("guides/pubg-mobile-skins-explained/index.html", "related-skins",
     "Latest PUBG Mobile skins and cosmetics", "New X-Suits, weapon skins, vehicle finishes and cosmetic announcements.",
     ("skins",), 5),
    ("guides/pubg-mobile-account-safety/index.html", "related-account-safety",
     "Account and GameLoop safety updates", "Read more about protecting accounts, logins and emulator setups.",
     ("account-security", "emulator"), 5),
    ("guides/pubg-mobile-uc-top-up-safety/index.html", "related-uc-safety",
     "UC purchases, draws and event advice", "Understand safer purchasing decisions and upcoming event rewards.",
     ("uc-safety",), 5),
    ("guides/index.html", "related-tutorials",
     "More gaming tutorials and how-to guides", "Explore practical tutorials from PUBG Mobile, GTA, CS2, VALORANT and gaming PCs.",
     ("tutorial",), None),
)

def relevant(posts, wanted, limit=None):
    """Latest dated posts first; prefer tutorials over previews on a date tie."""
    selected = [p for p in posts if set(p.get("topics", ())).intersection(wanted)]
    selected.sort(key=lambda p: p["slug"])
    selected.sort(key=lambda p: "tutorial" in p.get("topics", ()), reverse=True)
    selected.sort(key=lambda p: p["published"], reverse=True)
    return selected[:limit] if limit is not None else selected

def block(section_id, title, description, posts):
    cards = "\n".join(
        '<a href="/blog/' + p["slug"] + '/"><strong>' + html.escape(p["title"]) +
        '</strong><span>' + html.escape(p["summary"]) + '</span></a>'
        for p in posts
    )
    if not cards:
        cards = '<p>More articles will appear here as they are published.</p>'
    return "\n".join((
        START,
        '<section class="related-reading" aria-labelledby="' + section_id + '">',
        '<h2 id="' + section_id + '">' + html.escape(title) + '</h2>',
        '<p>' + html.escape(description) + '</p>',
        '<div class="cards">',
        cards,
        '</div>',
        '</section>',
        END,
    ))

def build_related_guides(root, write, posts):
    root = Path(root)
    for rel, section_id, title, description, topics, limit in TARGETS:
        file = root / rel
        original = file.read_text(encoding="utf-8")
        markup = block(section_id, title, description, relevant(posts, topics, limit))
        if START in original or END in original:
            if original.count(START) != 1 or original.count(END) != 1:
                raise ValueError(f"Guide generated markers are inconsistent: {rel}")
            pattern = re.compile(re.escape(START) + r"[\s\S]*?" + re.escape(END))
            result, count = pattern.subn(lambda _: markup, original)
            if count != 1:
                raise ValueError(f"Could not update related guide section: {rel}")
        else:
            if original.count("</article>") != 1:
                raise ValueError(f"Missing unique closing article tag: {rel}")
            result = original.replace("</article>", markup + "\n</article>", 1)
        write(rel, result)
