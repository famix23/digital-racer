# Google AdSense launch checklist for Digital Racer

## Current state
This branch adds About, Contact, Terms and Privacy pages, storefront footer links, and includes policy pages in the generated sitemap. **Ads are not active yet.** The site is not claimed to be Google-approved.

## Owner steps
1. Visit https://adsense.google.com/ and sign in or sign up with your own Google account.
2. Add `https://www.digitalracer.store` under Sites and follow Google's site verification instructions.
3. Obtain the actual AdSense publisher ID (format: `pub-XXXXXXXXXXXXXXXX`). Never guess this ID.
4. If Google instructs you to verify with the AdSense script, add this within the `<head>` of the site's HTML template(s), **with your real ID**:
   `<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>`
   The static homepage, catalog, generic product page and generated product pages have separate HTML heads. For generated pages, integrate the snippet with `scripts/build_seo.py`, then regenerate output to keep the changes persistent.
5. Create a root `ads.txt` file *only after the real publisher ID is known*, containing the exact AdSense authorization record Google provides, typically:
   `google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0`
   Check `https://www.digitalracer.store/ads.txt` after deployment.
6. Configure privacy and consent disclosures to match actual technologies. If serving personalized ads to EEA, UK or Swiss visitors, use an appropriate Google-certified CMP as required by Google. Review the privacy policy for accuracy before launch.
7. Submit for site review within AdSense and wait for Google's decision. After approval, configure auto ads or ad units and check the layout.

## Important quality and policy risks
- Existing catalog is predominantly product listings, so add meaningful original editorial content (buyer guides, game information, comparisons) before submission, without copying supplier descriptions.
- Several listings offer game accounts and rank services; game publishers may prohibit account transfer or other activity. Check the publisher terms and Google publisher policies. AdSense approval is not guaranteed by completing technical steps.
- Confirm the business's legal address, refund commitments, supported payment methods and applicable disclosures before adding any specific claims. The drafted public pages intentionally do not invent these.
- Keep advertising separate from WhatsApp checkout buttons. Avoid deceptive placement, invalid clicks or ad incentives.
- Do not activate ads until the correct publisher account, site authorization, consent implementation and Google approval are all in place.

## Site build
```sh
python scripts/build_seo.py
python scripts/build_seo.py --check
node scripts/test_storefront.cjs
```
