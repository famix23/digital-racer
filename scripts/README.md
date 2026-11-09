# Catalog maintenance

The storefront is a static website. The admin edits `inventory.json` through GitHub; it is not an order, payment or stock database.

After changing inventory or templates, run from the repository root:

```sh
python scripts/build_images.py
python scripts/build_seo.py
python scripts/build_seo.py --check
node scripts/test_storefront.cjs
node scripts/test_legacy_product_redirects.cjs
```

The image step requires Pillow. It creates content-addressed 480px and 960px WebP copies for primary product photos and never overwrites originals. Enlarged photos use originals. The SEO step uses only Python's standard library (Python 3.12 or later), preserves existing product routes, and generates product pages, homepage/catalog cards, metadata, structured data and the sitemap. Commit generated files with source changes.

CMS-only additions render in the browser, but their canonical pages and optimized images need this build before deployment. Configure the hosting build pipeline to run it when a suitable Python/Pillow runtime is available; the checked-in output remains deployable without that runtime.

`test_storefront.cjs` uses only Node built-ins. It checks malicious text/image inputs, JavaScript syntax, unique product lookup, price agreement and canonical-page indexability. Also verify search, filters, gallery keyboard controls and Buy Now links in a browser before publishing template changes.

The CMS dependency is version-pinned with an SRI hash in `admin/index.html`. Update its version and integrity together, then verify the sign-in screen and normal editing workflow. Never commit access tokens. `_headers` supplies baseline Cloudflare security headers and admin noindex directives; it does not replace authentication or a complete CSP that restricts script sources.

## Legacy product query URLs and Google canonicalization

The canonical product URL is `/p/<slug>/`. Cloudflare Workers runs `src/worker.mjs` **only** before `/product` and `/product.html` requests, where it permanently redirects exact, unambiguous `?item=<title>` matches to the current canonical `/p/` URL found in `p/index.json`. Three known legacy title aliases are handled explicitly. Unknown, ambiguous or title-less URLs continue using the existing generic noindex fallback. The script never redirects unrelated routes, edits product titles or accepts arbitrary external destinations.

Keep `src` excluded from the public static asset upload via `.assetsignore`. The `assets.binding`/`run_worker_first` Cloudflare configuration is required for server-side redirects. If the site uses a different deploy backend, these redirects must be implemented there separately; a Netlify static preview does not execute the Cloudflare Worker. Verify a real 301 on the production domain after deployment. The Google Search Console `noindex` example count may take time to update because Google must recrawl the old URLs.
