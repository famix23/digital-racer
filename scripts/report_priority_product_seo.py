#!/usr/bin/env python3
"""Prioritize verified high-intent DigitalRacer product pages for search-readiness checks.

This reports public canonical URL health from the published static files.
It DOES NOT submit Google indexing requests or claim these URLs are indexed.
Supplier descriptions, prices, listings and page markup are never edited.
"""
from __future__ import annotations

from collections import defaultdict
from html import unescape
from pathlib import Path
import json
import os
import re

ROOT = Path(__file__).resolve().parents[1]
HOST = "https://www.digitalracer.store"
CATEGORY_LIMITS = {"Account": 12, "Car Card": 8, "UC Top-Up": 4}
CHECKS = {
    "Account": [
        (r"glacier(?:\s+|[- ])?m416|m416(?:\s+|[- ])?glacier", 7),
        (r"x[- ]?suits?", 5),
        (r"mythics?|ultimate|gunlabs?", 2),
        (r"conqueror|collection|level|lvl", 1),
    ],
    "Car Card": [
        (r"bentley|ferrari|bugatti|porsche|lamborghini|mclaren|aston martin", 6),
        (r"car|vehicle|skin|card|gift", 2),
    ],
    "UC Top-Up": [(r"uc|unknown cash|top[- ]?up", 5)],
}


def rank(item, entry):
    if item.get("reference_only") is True or item.get("availability_unverified") is True:
        return -1
    category = item.get("category", "")
    patterns = CHECKS.get(category, [])
    terms = str(item.get("title", "")) + " " + str(item.get("description", ""))
    score = sum(weight for expression, weight in patterns if re.search(expression, terms, re.I))
    # Prefer exact, specific listing terms over unrelated generic category claims.
    if "pubg mobile" in terms.casefold():
        score += 1
    return score


def main():
    inv = json.loads((ROOT / "inventory.json").read_text(encoding="utf-8"))
    items = inv if isinstance(inv, list) else inv["items"]
    manifest = json.loads((ROOT / "p/index.json").read_text(encoding="utf-8"))
    assert len(items) == len(manifest)
    candidates = defaultdict(list)
    for index, (item, entry) in enumerate(zip(items, manifest)):
        assert entry["title"] == item["title"]
        category = item.get("category")
        if category not in CATEGORY_LIMITS:
            continue
        score = rank(item, entry)
        if score <= 0:
            continue
        candidates[category].append((score, index, entry))
    selected = []
    for category, limit in CATEGORY_LIMITS.items():
        for _, _, item in sorted(candidates[category], key=lambda x: (-x[0], -x[1]))[:limit]:
            path = ROOT / item["url"].lstrip("/") / "index.html"
            html = path.read_text(encoding="utf-8")
            url = HOST + item["url"]
            assert '<link rel="canonical" href="' + url + '">' in html, url
            assert 'name="description"' in html, url
            assert '<script type="application/ld+json">' in html, url
            assert '<h1 class="main-title" id="prod-title">' in html, url
            assert 'name="robots" content="noindex' not in html, url
            selected.append((category, item))
    assert len(selected) >= 15, "Not enough qualified product pages"
    result = [f"Search-readiness priority report: {len(selected)} canonical products (NOT Google index status)."]
    summary = ["## Search-ready product priorities", "",
               "These real listings have verified canonical HTML and product metadata. "
               "The list is **not** a Google Indexing API submission or proof of indexing.", ""]
    for category, item in selected:
        url = HOST + item["url"]
        result.append(f"{category}: {url}")
        title = unescape(item["title"]).replace("[", "(").replace("]", ")").replace("|", " ")[:100]
        summary.append(f"- **{category}:** [{title}]({url})")
    output = "\n".join(result)
    print(output, flush=True)
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n".join(summary) + "\n")


if __name__ == "__main__":
    main()
