# DigitalRacer Instagram launch

Status: DRAFTS PREPARED, NOT PUBLISHED. Created 2026-11-12.

## Proposed account identity

- Handle candidate: @digitalracer.store (availability not checked; not reserved)
- Display name: DigitalRacer | PUBG Mobile Marketplace
- Website: https://www.digitalracer.store/catalog
- Bio: PUBG Mobile Marketplace | Accounts, Car Skins, UC & Items | Worldwide enquiries | Browse catalog below
- Visual identity: black #050505 and gold #D4AF37, matching the current DR favicon.
- Highlights: START HERE, ACCOUNTS, CARS, UC, ITEMS, FAQ, CONTACT.

## Pinned launch grid (9 posts)

1. Welcome to DigitalRacer.
2. Browse all products: website catalog and live prices.
3. Accounts category showcase (confirm eligibility and platform terms first).
4. Car skins and car cards category.
5. UC top-up category with purchase safety notice.
6. In-game items category.
7. Popularity offers category.
8. Rank-related services (post only where allowed).
9. How to enquire and verify availability, region and delivery.

Pin 1, 2 and 9 after publishing. Use images from the real catalog, not fabricated item previews.

## Source and scheduling

The GitHub database has 506 products, and its product URL index matches all 506.
The public indexed page has displayed 453; confirm any mismatch before selling.
This branch includes eight CSV parts containing original catalog titles, prices, image URLs
and clean product URLs, with every entry marked as DRAFT_NOT_PUBLISHED / UNVERIFIED / REVIEW_REQUIRED.

Running python scripts/export_instagram.py regenerates 506 draft captions and URLs from
inventory.json and p/index.json. The GitHub Action, when merged, will rebuild an
artifact on catalog changes, on demand, and daily. It uploads draft files ONLY; it
never registers accounts, publishes to Instagram, or changes the production website.

## Publishing safeguards

Verify current stock, price, regional eligibility and the seller's rights to use each image;
check images for supplier contact details. Do not misrepresent the store as officially
affiliated with PUBG Mobile. Review Instagram/Meta rules and game terms, particularly
for account transfers and rank boosting. Never claim a sale, delivery, endorsement or review
that did not occur.

## Instagram connection blocker

The connected Metricool brand, Pubg mobile game mart, currently has a Facebook connection
but no Instagram connection. There is no Instagram registration/browser session available
in this conversation. Account creation and provider-required email/phone verification
remain incomplete, therefore no profile or posts are live.
