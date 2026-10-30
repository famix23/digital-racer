# Google AdSense setup for Digital Racer

## Installed
Publisher: `ca-pub-3636750354534911` (provided by the owner).
Every HTML head includes the asynchronous Google AdSense loader exactly once.
The root `ads.txt` authorizes `pub-3636750354534911` through Google:
`google.com, pub-3636750354534911, DIRECT, f08c47fec0942fa0`.

`scripts/build_seo.py` preserves the loader in generated storefront and product pages,
redirect pages, and standalone HTML pages, and writes the authorization file.
The integration does not establish Google approval, Auto ads settings, consent
configuration, ad delivery or earnings.

## Build and verify
```sh
python3 scripts/build_seo.py
python3 scripts/build_seo.py --check
node scripts/test_storefront.cjs
python3 scripts/test_adsense.py
```
After deployment, check the homepage, catalog, product URLs and
https://www.digitalracer.store/ads.txt on the actual production host.
Confirm HTTP success, exactly one correct loader within each HTML head,
and the plain-text authorization record rather than a fallback HTML page.

## Owner account steps
1. Add or confirm digitalracer.store in your AdSense account and request site review.
2. Check that Google recognizes the publisher code and ads.txt authorization.
3. Confirm the site's status in AdSense; only Google can approve the site.
4. Configure Auto ads in AdSense when eligible; installing the script alone does
   not confirm that Auto ads is enabled or ads will appear.
5. Configure Google's required consent messages or a Google-certified CMP for
   EEA, UK and Swiss visitors as applicable before serving relevant ads, and
   keep the privacy policy accurate. The repository does not configure a CMP.

Avoid clicking your own ads or encouraging clicks. Keep ads clear of order
controls. Review Google publisher policies and the relevant game publisher
terms for the catalog's accounts and services. Technical installation does
not guarantee approval.
