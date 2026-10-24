#!/usr/bin/env python3
"""
Optional: shrink oversized product images IN PLACE (same file name, same format,
so every path in inventory.json keeps working).  Requires Pillow:  pip install pillow

    python3 scripts/optimize_images.py            # optimize
    python3 scripts/optimize_images.py --dry-run  # just report

Only images referenced by inventory.json and larger than MIN_BYTES are touched.
JPEG: longest side capped at MAX_SIDE px, re-encoded at quality 82 (progressive).
PNG:  longest side capped at MAX_SIDE px, saved losslessly (no colour reduction).
A file is only replaced when the result is at least 15% smaller. Originals stay in git history.
"""
import io
import json
import os
import sys

from PIL import Image, ImageOps

MAX_SIDE = 1600
MIN_BYTES = 350_000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY = "--dry-run" in sys.argv

data = json.load(open(os.path.join(ROOT, "inventory.json"), encoding="utf-8"))
items = data if isinstance(data, list) else data.get("items", [])
paths = set()
for it in items:
    for p in [it.get("thumbnail")] + list(it.get("gallery") or []):
        if p and not str(p).startswith("http"):
            paths.add(str(p).strip().lstrip("/"))

saved = 0
for rel in sorted(paths):
    full = os.path.join(ROOT, rel)
    if not os.path.isfile(full) or os.path.getsize(full) < MIN_BYTES:
        continue
    before = os.path.getsize(full)
    im = Image.open(full)
    fmt = im.format
    if fmt not in ("JPEG", "PNG"):
        continue
    im = ImageOps.exif_transpose(im)
    w, h = im.size
    scale = min(1.0, MAX_SIDE / max(w, h))
    if scale < 1:
        im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    if fmt == "JPEG":
        im.convert("RGB").save(buf, "JPEG", quality=82, optimize=True, progressive=True)
    else:
        im.save(buf, "PNG", optimize=True)
    after = len(buf.getvalue())
    if after > before * 0.85:
        continue
    saved += before - after
    print(f"{before // 1024:>6} KB -> {after // 1024:>5} KB  {im.size[0]}x{im.size[1]}  {rel}")
    if not DRY:
        with open(full, "wb") as f:
            f.write(buf.getvalue())
print(f"total saved: {saved / 1e6:.1f} MB{' (dry run)' if DRY else ''}")
