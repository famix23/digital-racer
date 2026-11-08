# Digital Racer: AI-friendly gaming blog publishing

Blog articles are stored as plain-text JSON under content/blog. The build generates /blog/ and /blog/<slug>/ independently of inventory.json, product prices or product-page SEO.

For a new article, create content/blog/my-new-topic.json using the same structure as the existing samples: slug, title, summary, category, published (YYYY-MM-DD), intro, and a list of sections. Each section includes a heading, an array of paragraphs, and optional points. Write a substantial original article with verified details. No copied content, HTML, external URLs, fake experiences, fabricated statistics or promotional links.

Run python3 scripts/build_seo.py. Commit both the source JSON and generated blog pages, the updated blog index and sitemap. Verify with python3 scripts/build_seo.py --check, python3 scripts/test_content_quality.py, python3 scripts/test_adsense.py and node scripts/test_storefront.cjs. Submit changes through a pull request for owner approval before deployment.

The generator escapes all article text and rejects URL strings, markup and thin content. External research is permissible while writing, but published articles contain only links within DigitalRacer.store. Technical AdSense and canonical metadata remain intact.

Never use this article workflow to modify inventory.json, generated product directories under p/, or the catalog SEO card blocks.
