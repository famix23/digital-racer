# SEO build scripts

## After every catalog change (inventory.json)

```bash
python3 scripts/build_seo.py
git add -A && git commit -m "Rebuild SEO pages" && git push
```

`build_seo.py` uses only the Python standard library. It regenerates:

| Output | What it is |
| --- | --- |
| `p/<slug>/index.html` | Pre-rendered product page at `/p/<slug>/` (copy of `product.html` with the real title, price, images, description, meta tags and Product / BreadcrumbList JSON-LD filled in). Old pages for removed products are deleted. |
| `p/index.json` | title + price → clean URL map. The site's JavaScript uses it to link cards to `/p/<slug>/`; items not in it fall back to `product.html?item=…`. |
| `index.html`, `catalog.html`, `product.html` | Only the blocks between `<!-- SEO:HEAD:BEGIN … -->`/`<!-- SEO:HEAD:END -->` and `<!-- SEO:GRID:… -->` markers. Edit everything else as usual; don't hand-edit inside the markers. |
| `sitemap.xml`, `robots.txt` | All pages + every product (with image entries). |

`python3 scripts/build_seo.py --check` exits 1 if the generated files are out of date (no writes).

Site-wide titles/descriptions and the canonical host (`https://www.digitalracer.store`) are set at the top of `build_seo.py`.

If the catalog is edited in /admin and the script isn't re-run, nothing breaks: product pages still
load live data from `/inventory.json`, and new products link to `product.html?item=…` until the
next rebuild. Slugs come from the product title, so renaming a product changes its URL.

## Optional: shrink big images

```bash
pip install pillow
python3 scripts/optimize_images.py --dry-run   # report only
python3 scripts/optimize_images.py             # rewrite in place (same file names)
```

Image policy: upload product photos in HD (long side at least 1280px, ideally 1920px).
`optimize_images.py` never upscales and never shrinks a long side below 1920px.
Keep product images at their original resolution. Do not upscale them to fake HD.

## Optional: rebuild automatically on every push (GitHub Actions)

Saving this as `.github/workflows/build-seo.yml` would rebuild after any push that changes
`inventory.json` (including CMS edits) and commit the result back to the branch:

```yaml
name: Build SEO pages
on:
  push:
    paths: ["inventory.json", "product.html", "index.html", "catalog.html", "scripts/build_seo.py"]
permissions:
  contents: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 scripts/build_seo.py
      - run: |
          git config user.name "seo-bot"
          git config user.email "seo-bot@users.noreply.github.com"
          git add -A
          git diff --cached --quiet || (git commit -m "Rebuild SEO pages" && git push)
```
