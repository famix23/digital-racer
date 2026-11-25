# GameBoost → DigitalRacer: verified catalog imports

This is a source-data import path for GameBoost reseller listings that the DigitalRacer owner has independently obtained with the necessary permission. **It does not scrape GameBoost, bypass logins, read marketplace private data or claim that a public listing is currently in stock.** It does not run automatically.

## Why a validated source export is required

GameBoost's public results view is not a complete, reliable per-listing source of original description, pictures, price in DigitalRacer's USD currency, or stock. Importing search-card snippets as products would violate the DigitalRacer rule to preserve full reseller details and could advertise incorrect inventory. Before importing, obtain the authorized seller's complete original product records and photos, and confirm they are orderable.

## Accepted JSON structure

```json
{
  "items": [
    {
      "id": "supplier-unique-987654",
      "title": "EXACT ORIGINAL SELLER TITLE, INCLUDING EMOJIS",
      "description": "Entire seller description as written, including item lists, restrictions and transfer conditions.\nContact seller by WhatsApp +11234567890",
      "price_usd": "189.00",
      "currency": "USD",
      "category": "Account",
      "account_level": "75",
      "tag": "GLOBAL",
      "verified_instant_delivery": false,
      "photos": ["supplier-unique-987654/1.jpg", "supplier-unique-987654/2.jpg"]
    }
  ]
}
```

The JSON's `photos` values are paths relative to the local reviewed photo directory. Photos must depict that exact listing, be visually checked for any embedded reseller phone/social contact, and be JPEG, PNG or WebP files. No remote-hosted photos, default placeholders, source URLs, seller ratings, claims or third-party checkout links are inserted into public catalog records.

## Operator steps

1. Acquire a legitimately authorized reseller export with **complete** descriptions, original photos, confirmed availability, and verified USD prices. Do not use an incomplete search-results scrape. Put the images in a local temporary directory and check for embedded seller contact details.
2. Dry-run: `python3 scripts/import_authorized_reseller.py --feed /path/to/export.json --images-dir /path/to/reviewed-images --report /tmp/digitalracer-gameboost-report.json`
3. Apply only after checking the report: `python3 scripts/import_authorized_reseller.py --feed /path/to/export.json --images-dir /path/to/reviewed-images --apply --report /tmp/digitalracer-gameboost-report.json`
4. Rebuild: `python3 scripts/build_images.py && python3 scripts/build_seo.py && python3 scripts/build_seo.py --check`. Run `python3 scripts/test_authorized_reseller.py`, `python3 scripts/test_product_titles.py`, `node scripts/test_storefront.cjs`, and the repository's indexing/SEO tests. Commit the catalog, images, and generated pages together in a reviewable PR. Publish only verified, currently orderable products.

## Guarantees and limits

- Keeps the reseller-written Unicode title exactly in both `title` and `source_title`, with no SEO prefixes.
- Keeps full product details, while removing standalone supplier contact lines. Rejects ambiguous contact + product-fact lines rather than destroying information.
- Adds DigitalRacer's `+923454342911` WhatsApp number to each cleaned description.
- Requires a stable supplier listing ID; skips already imported IDs and duplicate existing titles. Never deletes/rekeys legacy products.
- Never treats EUR or other currencies as USD. Only explicitly verified USD prices are supported.
- Refuses PUBG PC/Steam accounts in PUBG Mobile's category, empty photos, missing descriptions and paths escaping the reviewed photo directory.
- Writes only to `inventory.json` and copies reviewed local photo files when `--apply` is specified. **It does not regenerate SEO pages for you**, so the build is mandatory.
- Image contact details cannot be reliably erased by text filtering: the images must be inspected/edited before importing. The import script does not claim to check live source availability, verify account ownership or enforce game-platform transfer rules.