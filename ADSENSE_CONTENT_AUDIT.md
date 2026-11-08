# Digital Racer — AdSense low-value-content review (8 November 2026)

## Observed
- AdSense dashboard screenshot supplied by owner shows **Needs attention → Low value content**, while **ads.txt = Authorized**.
- The storefront's home page is mostly offer cards and prices. The catalog has 353 product entries, including third-party sourced item descriptions. The presence or originality of every source description has not been independently verified.
- The existing About, Contact, Terms, and Privacy pages are useful foundations and were already present.
- PUBG Mobile's EULA prohibits account transfers; its support pages warn of penalties for unauthorized UC transactions. Adding content cannot eliminate this fundamental category risk.

## Changes proposed in this branch
- Three independently readable guides plus an overview, each with titles, descriptions, canonicals, structured data, publisher references, and clear warnings.
- Guide navigation in the storefront, catalog and About page.
- Include editorial URLs in deterministic sitemap generation and preserve them during build.
- New automated structural checks in the GitHub pull-request workflow.

## Remaining work (requires editorial or business-owner action)
1. Review each of the 353 catalog items for first-hand verification, accurate title, stock status, product detail, price, rights to imagery and original descriptions. Don't manufacture testimonials or unique data.
2. Reconcile account and UC listings with the game's publisher terms. Decide whether categories contrary to publisher rules should be withdrawn or separated from any monetized editorial pages. This branch intentionally does not silently delete inventory.
3. Make refund, payment, delivery and complaint policies precise enough to match real business operations; do not promise protections that aren't actually offered.
4. Confirm the hosting deployment is correct, submit sitemap in Search Console, request re-review in AdSense, and check Policy Center. Only Google can approve the site.
5. Reassess content quality through actual user feedback and search queries, rather than generating large quantities of low-information articles.

## Official references
- Google AdSense eligibility: https://support.google.com/adsense/answer/9724
- Google helpful content guidance: https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- PUBG Mobile EULA: https://www.pubgmobile.com/PK/terms.shtml
- PUBG Mobile UC purchase warning: https://pubgmobile.helpshift.com/hc/en/4-support/faq/304-penalties-about-purchase-through-unauthorized-services/

## Tests
Run after checking out this branch:
```sh
python3 scripts/build_seo.py --check
python3 scripts/test_adsense.py
python3 scripts/test_content_quality.py
node scripts/test_storefront.cjs
```
The existing GitHub pull request workflow runs these checks plus a deterministic rebuild.
