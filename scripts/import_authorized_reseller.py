#!/usr/bin/env python3
"""Safely import an authorized reseller JSON export into DigitalRacer inventory.

No scraping, no network calls, no external dependencies. The source must provide
complete per-listing product details, prices in USD, and locally reviewed photos.

Usage:
  python scripts/import_authorized_reseller.py --feed vendor-export.json --images-dir ./reviewed-photos
  python scripts/import_authorized_reseller.py --feed vendor-export.json --images-dir ./reviewed-photos --apply

The default is validation/dry-run. The --apply flag updates inventory.json and
copies verified local photos. Afterward run build_images.py and build_seo.py.
"""
import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'inventory.json'
PHOTO_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}
CONTACT = '+923454342911'

EMAIL = re.compile(r'(?<![\w.])[\w.+-]+@[\w.-]+\.[a-z]{2,}', re.I)
LINK = re.compile(r'(?i)(?:https?://|www\.|wa\.me/|t\.me/|discord\.gg/)[^\s<>]*')
CONTACT_LINE = re.compile(
    r'(?i)\b(?:whats?app|telegram|instagram|discord|snapchat|contact\s+(?:me|us|seller)|'
    r'follow\s+(?:me|us)|seller\s+(?:phone|number|contact)|reach\s+(?:me|us)|'
    r'text\s+me|dm\s+me|(?:call|message)\s+(?:me|us))\b|(?<!\w)(?:\+\d[\d\s().-]{8,}|@\w{4,})'
)
PRODUCT_FACT = re.compile(
    r'(?i)\b(?:lvl|level|mythic|x.?suit|glacier|m416|gunlab|vehicle|skin|'
    r'outfit|collection|conqueror|transfer|linked|login|recovery|region|server|'
    r'email\s+access|full\s+access|delivery\s+time|restricted)\b'
)
SUPPLIER_PROMO = re.compile(r'(?i)\b(?:why\s+buy\s+from\s+us|our\s+store\s+rating|seller\s+reviews)\b')


def cleaned_description(raw):
    """Preserve all item details; fail closed if a contact line mixes with facts."""
    if not isinstance(raw, str) or len(raw.strip()) < 15:
        raise ValueError('Full supplier description is missing/too short')
    cleaned, redactions = [], []
    for rawline in raw.replace('\r\n', '\n').split('\n'):
        line = rawline
        if SUPPLIER_PROMO.search(line):
            raise ValueError('Supplier promotional section requires human review')
        if CONTACT_LINE.search(line):
            # Skip a pure contact/marketing line but do NOT discard product data.
            if PRODUCT_FACT.search(line):
                raise ValueError('Contact information mixed with item/transfer facts; clean source line manually')
            redactions.append(rawline)
            continue
        line = LINK.sub('', line)
        line = EMAIL.sub('', line)  # Does not remove 'email access' transfer notes.
        if line != rawline:
            redactions.append(rawline)
        cleaned.append(line.rstrip())
    body = '\n'.join(cleaned).strip()
    if len(body) < 15 or EMAIL.search(body) or LINK.search(body) or CONTACT_LINE.search(body):
        raise ValueError('Description is empty or supplier contact remains')
    return body + '\n\nBuy now on WhatsApp: ' + CONTACT, redactions


def price_usd(row):
    currency = str(row.get('currency', 'USD')).upper().strip()
    if currency != 'USD':
        raise ValueError(f'Price must be verified in USD; found {currency!r}; no silent FX conversion')
    original = str(row.get('price_usd', row.get('price', ''))).strip()
    if not re.fullmatch(r'\d+(?:\.\d{1,2})?', original):
        raise ValueError('Missing/invalid USD price (expected number without currency symbols)')
    try:
        price = Decimal(original)
    except InvalidOperation:
        raise ValueError('Invalid USD price') from None
    if not (Decimal('0.01') <= price <= Decimal('1000000')):
        raise ValueError('USD price out of range')
    return f'{price:.2f}'


def safe_photo(path, images_dir):
    if not isinstance(path, str) or not path or path.startswith(('http:', 'https:', '//')):
        raise ValueError('Photo must be a locally downloaded, visually reviewed file')
    rel = Path(path)
    if rel.is_absolute() or '..' in rel.parts or rel.suffix.lower() not in PHOTO_EXTS:
        raise ValueError('Photo file path/extension is unsafe')
    source = (images_dir / rel).resolve()
    if not source.is_relative_to(images_dir.resolve()) or not source.is_file():
        raise ValueError(f'Reviewed source photo not found: {path}')
    if not (1000 <= source.stat().st_size <= 20 * 1024 * 1024):
        raise ValueError(f'Photo size invalid: {path}')
    magic = source.read_bytes()[:16]
    if not (magic.startswith(b'\xff\xd8\xff') or magic.startswith(b'\x89PNG\r\n\x1a\n') or
            (magic.startswith(b'RIFF') and magic[8:12] == b'WEBP')):
        raise ValueError(f'Not a supported image: {path}')
    sha = hashlib.sha256(source.read_bytes()).hexdigest()[:20]
    target = ROOT / 'images' / 'uploads' / f'authorized-gameboost-{sha}{rel.suffix.lower()}'
    return source, target, '/images/uploads/' + target.name


def prepare_row(source, images_dir):
    if not isinstance(source, dict):
        raise ValueError('Entry must be an object')
    sid = str(source.get('id', source.get('supplier_listing_id', ''))).strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]{3,100}', sid):
        raise ValueError('Unique, stable reseller listing ID required')
    title = source.get('title')
    if not isinstance(title, str) or title.strip() != title or not title:
        raise ValueError('Exact nonempty seller-written title required; no modification allowed')
    if re.search(r'(?i)pubg\s+(?:steam|battlegrounds)|steam\s+account', title):
        raise ValueError('PUBG PC/Steam account cannot be imported into PUBG Mobile')
    category = source.get('category', 'Account')
    if category != 'Account':
        raise ValueError('This feed imports PUBG Mobile accounts only')
    description, redactions = cleaned_description(source.get('description'))
    photos = source.get('photos')
    if not isinstance(photos, list) or not photos or not all(isinstance(p, str) for p in photos):
        raise ValueError('At least one supplier-matching, visually reviewed photo is mandatory')
    copied = [safe_photo(photo, images_dir) for photo in photos]
    price = price_usd(source)
    level = source.get('account_level', '')
    if level and not re.fullmatch(r'\d{1,3}', str(level)):
        raise ValueError('account_level must be numeric, if provided')
    tag = str(source.get('tag', '')).strip()
    if tag and tag not in ('GLOBAL', 'NA', 'EU', 'ASIA', 'SEA', 'MENA'):
        raise ValueError('Region tag must be confirmed explicitly')
    row = {
        'title': title,
        'source_title': title,
        'listing_origin': 'reseller',
        'supplier_listing_id': 'gameboost-' + sid,
        'price': price,
        'category': 'Account',
        'tag': tag,
        'badge': 'INSTANT' if source.get('verified_instant_delivery') is True else '',
        'account_level': str(level) if level else '',
        'thumbnail': copied[0][2],
        'gallery': [p[2] for p in copied[1:]],
        'description': description,
        'preserve_description': True,
    }
    return row, copied, redactions


def import_feed(feed, images_dir, inventory_path=INVENTORY, apply=False):
    source = json.loads(Path(feed).read_text(encoding='utf-8'))
    entries = source if isinstance(source, list) else source.get('items')
    if not isinstance(entries, list):
        raise ValueError('Feed must contain an items list')
    current = json.loads(inventory_path.read_text(encoding='utf-8'))
    items = current if isinstance(current, list) else current.get('items')
    if not isinstance(items, list):
        raise ValueError('Existing inventory has no items list')
    titles = {x.get('title') for x in items}
    ids = {x.get('supplier_listing_id') for x in items if x.get('supplier_listing_id')}
    new, all_copies, redacted, ignored = [], [], [], []
    seen_ids = set()
    for n, raw in enumerate(entries, 1):
        try:
            row, photos, removals = prepare_row(raw, images_dir)
            if row['supplier_listing_id'] in seen_ids:
                raise ValueError('Repeated supplier listing ID within feed')
            seen_ids.add(row['supplier_listing_id'])
            if row['supplier_listing_id'] in ids or row['title'] in titles:
                ignored.append({'id': row['supplier_listing_id'], 'reason': 'existing listing, no overwrite'})
                continue
            new.append(row)
            all_copies.extend(photos)
            redacted.append({'id': row['supplier_listing_id'], 'contact_lines_removed': len(removals)})
            titles.add(row['title'])
        except ValueError as error:
            raise ValueError(f'Feed entry {n}: {error}') from error
    if apply:
        for src, dst, _ in all_copies:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                shutil.copyfile(src, dst)
        items.extend(new)
        inventory_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'current_products': len(items) - (len(new) if apply else 0),
            'feed_items': len(entries), 'new_products': len(new), 'duplicates_skipped': ignored,
            'contacts_cleaned': redacted, 'applied': apply,
            'instructions': 'Regenerate image variants, canonical pages, sitemap and run tests before publishing.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--feed', type=Path, required=True, help='Authorized supplier export JSON file')
    ap.add_argument('--images-dir', type=Path, required=True, help='Folder with reviewed photos matching feed paths')
    ap.add_argument('--apply', action='store_true', help='Write catalog and copy images; default dry-run')
    ap.add_argument('--report', type=Path, help='Optional private JSON report (do not commit)')
    args = ap.parse_args()
    try:
        results = import_feed(args.feed, args.images_dir, apply=args.apply)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print('IMPORT REJECTED:', error, file=sys.stderr)
        return 1
    result = json.dumps(results, indent=2, ensure_ascii=False)
    print(result)
    if args.report:
        args.report.write_text(result + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())