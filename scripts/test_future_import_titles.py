#!/usr/bin/env python3
"""Block newly imported reseller listings whose titles differ from the saved seller text.

Compare the proposed inventory with an earlier Git revision. Existing products are
exempt; do not rewrite historical titles or re-key canonical URLs.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def products_from_json(raw):
    data = json.loads(raw)
    return data if isinstance(data, list) else data["items"]


def identity(p):
    # Price and descriptions change independently of the stable listing.
    return (p.get("title"), p.get("thumbnail", p.get("image", "")))


def newly_introduced(old, current):
    existing = Counter(identity(p) for p in old)
    for product in current:
        fingerprint = identity(product)
        if existing[fingerprint]:
            existing[fingerprint] -= 1
        else:
            yield product


def validation_errors(new_items):
    errors = []
    for p in new_items:
        title = p.get("title")
        origin = p.get("listing_origin") or "reseller"
        if not isinstance(title, str) or not title.strip():
            errors.append("New product has no title")
            continue
        if origin not in ("reseller", "original"):
            errors.append(f"{title!r}: listing_origin must be reseller or original")
        elif origin == "reseller":
            supplied = p.get("source_title")
            if not isinstance(supplied, str) or not supplied:
                errors.append(f"{title!r}: reseller import requires source_title copied verbatim")
            elif supplied != title:
                errors.append(f"{title!r}: title must match source_title exactly; do not add SEO prefixes, paraphrase, shorten, reformat or change emojis")
    return errors


def self_test():
    base = [{"title": "Old account", "thumbnail": "/img/a.png", "price": "15"}]
    exact = {"title": "✨ PUBG Mobile Account | M416 Lv 7 — 99 Mythics",
             "source_title": "✨ PUBG Mobile Account | M416 Lv 7 — 99 Mythics",
             "thumbnail": "/img/new.png", "listing_origin": "reseller"}
    assert list(newly_introduced(base, base + [exact])) == [exact]
    assert not validation_errors([exact])
    assert not validation_errors([{**exact, "listing_origin": "original", "source_title": None}])
    assert validation_errors([{**exact, "title": "PUBG Mobile Account – " + exact["title"]}])
    assert validation_errors([{**exact, "title": exact["title"].replace("✨", "")}])
    assert validation_errors([{**exact, "source_title": None}])
    assert validation_errors([{**exact, "listing_origin": "unknown"}])
    assert list(newly_introduced(base, [{**base[0], "price": "21"}])) == []
    assert list(newly_introduced(base, base + [base[0]])) == [base[0]]
    print("Passed: source-title enforcement and Unicode / authentic PUBG title exceptions.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=os.environ.get("DR_INVENTORY_BASE"),
                        help="Baseline Git commit SHA with previous inventory.json")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    self_test()
    if args.self_test:
        return 0

    if not args.base or set(args.base) == {"0"}:
        parser.error("Specify --base or DR_INVENTORY_BASE; cannot validate new imports without earlier inventory")

    try:
        before = subprocess.check_output(
            ["git", "show", f"{args.base}:inventory.json"], cwd=ROOT, text=True,
            encoding="utf-8")
    except subprocess.CalledProcessError as exc:
        parser.error(f"Cannot fetch baseline inventory from Git: {exc}")

    after = (ROOT / "inventory.json").read_text(encoding="utf-8")
    added = list(newly_introduced(products_from_json(before), products_from_json(after)))
    errors = validation_errors(added)
    for err in errors:
        print("ERROR:", err, file=sys.stderr)
    if errors:
        print(f"Failed: {len(errors)} source-title issue(s) in {len(added)} new/renamed listings.", file=sys.stderr)
        return 1
    print(f"Passed: {len(added)} newly introduced listings preserve exact reseller title text.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
