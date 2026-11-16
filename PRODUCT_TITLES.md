# DigitalRacer title preservation

## Product imports

Use **the original title written by the seller** as the inventory \`title\` for every category. Retain exact wording, capitalization, punctuation, emojis and item counts. Never prepend "PUBG Mobile Account", "Car Card", "UC", keywords, prices or delivery claims just for SEO. Do not remove a PUBG Mobile phrase that already exists in a seller's own title.

If an existing inventory entry needs to keep its historical internal identity or URL while showing a verified source title, add the exact text under \`original_title\`, \`source_title\` or \`seller_title\`. The product builder prefers that text for the visible heading, cards, accessibility text and Product structured data but keeps the original title for lookup and the canonical URL slug.

For legacy account summaries whose heading appears to have received an extra **PUBG Mobile Account** prefix during earlier DigitalRacer imports, `content/product-title-overrides.json` contains an explicit display-only mapping of the 201 affected inventory titles. This removes the repetitive prefix from the storefront but **does not claim the remaining summary is the verified verbatim reseller title**. These mappings are frozen to existing titles only; new imported products are never automatically stripped. Inventory titles and URLs remain unchanged. A verified `original_title`, `source_title`, or `seller_title` always overrides the legacy display correction, even if the authentic reseller wording contains PUBG Mobile Account. Do not use general regex stripping for future imports.

## Mandatory future reseller imports

**Applies to all future additions from reseller websites** (ZeusX, GameBoost or any other source): copy the reseller's full title **verbatim** into BOTH `title` and `source_title`. Preserve the exact capitalization, punctuation, spacing, symbols, emojis, numbers and even `PUBG Mobile Account` when it actually appears on the source website. Never prepend or remove game keywords, strip emojis, shorten the title, invent product claims, append price or delivery promises, or generate an SEO title in place of the seller's words.

Use `listing_origin: reseller` (or leave absent, since reseller is the default). For a genuinely DigitalRacer-original product not sourced from a third party, use `listing_origin: original`. Never mark copied products as original just to bypass checking.

`scripts/test_future_import_titles.py` compares each proposed inventory with the preceding Git revision. Every new or renamed reseller listing must have a nonempty `source_title` **exactly equal** to its `title`, including emojis and meaningful punctuation. The pull-request/push workflow rejects additions missing this data or where a paraphrased / SEO-padded title differs. The check cannot independently prove what the external website currently displays: the importer must copy and verify the source before posting.

The pre-existing 645-product inventory is grandfathered; no existing title, price, canonical URL or image is modified by this rule. The 201 historical display-only overrides apply only to their exact legacy keys. A genuine source title stored in `source_title` or `original_title` takes priority over them; a future reseller title that really includes `PUBG Mobile Account` therefore remains intact.

SEO category names, descriptions and structured metadata may contain relevant game words **separately**. Do not insert marketing or SEO words into a supplied title. New products still need a static regeneration (`python3 scripts/build_seo.py`) and a published build before their canonical pages reflect the title.

## Correcting an older title in the admin editor

The `/admin/` catalog editor includes an optional **Original Reseller Title** field. For a product that already has an established canonical link, keep its existing internal `title` unchanged and enter the verified seller's exact text in `original_title`. The storefront and next static generation use `original_title` for the visible display. The internal title remains the lookup key, so the existing URL, product price, photos and order mapping are unaffected.

For **new** products, paste the reseller's verbatim text directly into `title`; leave `original_title` empty. Do not paste a shortened SEO summary or mechanically remove an existing supplier-written phrase.

Inventory edits alone do **not** regenerate all static pages. Run `python3 scripts/build_seo.py` and commit generated pages before expecting the updated H1, category cards and metadata to appear at the canonical URL.

## SEO metadata without title pollution

The generator uses category breadcrumbs, Product JSON-LD and an SEO meta description. Its category keyword introduction is conditional: it is only added to structured descriptions when the supplier description does not already mention PUBG Mobile. Source descriptions in inventory are left unchanged.

The generic In-Game Items category can cover other games; do not infer that every such item belongs to PUBG Mobile.

Run \`python3 scripts/build_seo.py\` after modifying inventory or title overrides, commit every generated page, and run \`python3 scripts/test_product_titles.py\`. Existing product URLs should not be renamed merely to remove keyword prefixes from displayed text.
