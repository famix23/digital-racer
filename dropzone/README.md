# Speed Drift Vehicle Gift Studio (presentation demo)

This folder is a standalone, responsive vehicle-gifting **mockup** integrated with DigitalRacer. It runs on the existing Cloudflare static-assets deployment at **/dropzone/**.

## What it does

1. Shows a searchable, filterable vehicle collection with Bentley, Lamborghini, Ferrari, Bugatti, Pagani, Dodge and selected gallery examples from other brands.
2. Loads a small selection of current DigitalRacer **Car Card** listing images and original titles from \`/inventory.json\` (read-only). No edits to inventory.
3. Collects example Player UID, character name, server and region in browser memory, with a 1–10 gift quantity selector.
4. Previews the selections, simulates a gift-dispatch progress animation and produces a conspicuously labeled **DEMO ONLY** summary.

## What it never does

- No real in-game gifting, account lookup or recipient authentication.
- No payments, purchase orders, payment credentials, passwords, OTPs or login tokens.
- No backend POST or retention of recipient data. Reloading the page clears the input.
- No official PUBG MOBILE affiliation or claim of current inventory for archived collaborations.
- No actual gift delivery confirmation.

## Files

- \`index.html\`: accessible interface, information hierarchy and demo disclaimers.
- \`style.css\`: responsive black-and-gold DigitalRacer design.
- \`catalog.js\`: historic model and finish examples; \`official\` denotes collaboration archive, \`store\` denotes DigitalRacer catalogue examples and \`example\` denotes unverified presentation examples.
- \`app.js\`: client-side event handlers, validation, optional storefront image gallery and local simulation.
- \`../scripts/test_dropzone_demo.cjs\`: static smoke checks.

Run \`node scripts/test_dropzone_demo.cjs\` from the repository root.

## Deployment / routing

The existing Worker in \`src/worker.mjs\` serves all non-legacy-product URLs through the Cloudflare ASSETS binding. Place \`dropzone/index.html\` in the repository as supplied. The homepage links to \`/dropzone/\`, and the page includes links back to the real catalog.

This page has an HTML noindex meta tag and a matching \`_headers\` rule. It is intentionally excluded from generated SEO pages and never edits \`scripts/build_seo.py\`, supplier titles, catalog, blog, product pages or payment flows.

## Images and naming

Where available, images are *reference photos* from existing DigitalRacer product/account listings, not guaranteed exact in-game finish icons. All other cards use an original CSS/SVG car illustration. Validate licensing, exact cosmetics, availability and screenshots before promoting this demo as a client deliverable.
