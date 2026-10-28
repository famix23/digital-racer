"""Build small, content-addressed storefront copies; never change original images.

Requires Pillow. Run before build_seo.py after adding catalog photos.
"""
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
inventory = json.loads((ROOT / 'inventory.json').read_text(encoding='utf-8'))
items = inventory if isinstance(inventory, list) else inventory['items']
out = ROOT / 'images/optimized'
out.mkdir(parents=True, exist_ok=True)
mapping = {}
original_bytes = optimized_bytes = 0
for item in items:
    raw = item.get('thumbnail') or item.get('image')
    if not raw or raw.startswith('https://'):
        continue
    url = '/' + raw.lstrip('/')
    source = (ROOT / unquote(url.lstrip('/'))).resolve()
    if not source.is_relative_to(ROOT) or not source.is_file():
        raise ValueError(f'Invalid thumbnail path: {raw}')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()[:20]
    variants = {}
    with Image.open(source) as original:
        original = ImageOps.exif_transpose(original).convert('RGB')
        for size in (480, 960):
            target = out / f'{digest}-{size}.webp'
            if not target.exists():
                image = original.copy()
                image.thumbnail((size, size), Image.Resampling.LANCZOS)
                image.save(target, 'WEBP', quality=84, method=6)
            # A compressed source can already be smaller than a derivative.
            variants[str(size)] = '/' + target.relative_to(ROOT).as_posix() if target.stat().st_size < source.stat().st_size else url
    mapping[url] = variants
    original_bytes += source.stat().st_size
    optimized_bytes += (ROOT / variants['480'].lstrip('/')).stat().st_size
assets = ROOT / 'assets'
assets.mkdir(exist_ok=True)
text = json.dumps(mapping, ensure_ascii=False, separators=(',', ':'))
(assets / 'image-map.json').write_text(text + '\n', encoding='utf-8')
(assets / 'image-map.js').write_text('window.DR_IMAGES = ' + text + ';\n', encoding='utf-8')
print(f'{len(mapping)} thumbnails: original {original_bytes:,} bytes; card copies {optimized_bytes:,} bytes ({100 * (1 - optimized_bytes / original_bytes):.1f}% smaller).')
