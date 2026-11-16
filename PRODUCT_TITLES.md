# DigitalRacer title preservation

## Product imports

Use **the original title written by the seller** as the inventory \`title\` for every category. Retain exact wording, capitalization, punctuation, emojis and item counts. Never prepend "PUBG Mobile Account", "Car Card", "UC", keywords, prices or delivery claims just for SEO. Do not remove a PUBG Mobile phrase that already exists in a seller's own title.

If an existing inventory entry needs to keep its historical internal identity or URL while showing a verified source title, add the exact text under \`original_title\`, \`source_title\` or \`seller_title\`. The product builder prefers that text for the visible heading, cards, accessibility text and Product structured data but keeps the original title for lookup and the canonical URL slug.

For specifically confirmed owner corrections where the vendor's original wording was **not stored**, use \`content/product-title-overrides.json\`. Do not apply regex stripping to 645 old titles: it can erase genuine seller titles. The screenshot-confirmed Fireman Set heading has one owner correction. To restore any other previously summarized product **exactly**, obtain the original seller title or listing page first.

## SEO metadata without title pollution

The generator uses category breadcrumbs, Product JSON-LD and an SEO meta description. Its category keyword introduction is conditional: it is only added to structured descriptions when the supplier description does not already mention PUBG Mobile. Source descriptions in inventory are left unchanged.

The generic In-Game Items category can cover other games; do not infer that every such item belongs to PUBG Mobile.

Run \`python3 scripts/build_seo.py\` after modifying inventory or title overrides, commit every generated page, and run \`python3 scripts/test_product_titles.py\`. Existing product URLs should not be renamed merely to remove keyword prefixes from displayed text.
