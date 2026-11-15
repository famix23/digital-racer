/* Shop navigation regression checks: all category links lead to product filters. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const read = p => fs.readFileSync(path.resolve(__dirname, '..', p), 'utf8');
const home = read('index.html');
const catalog = read('catalog.html');
const hubs = JSON.parse(read('content/shop-hubs.json'));
const nav = home.match(/<section class="dr-shop-categories"[\s\S]*?<\/section>/);
assert.ok(nav, 'Missing premium shopping category navigation');
const hrefs = [...nav[0].matchAll(/class="dr-shop-tile" href="([^"]+)"/g)].map(m => m[1]);
assert.equal(hrefs.length, hubs.length, 'Unexpected number of shopping buttons');
for(const hub of hubs){
  const href = '/catalog?category=' + encodeURIComponent(hub.category);
  assert.ok(hrefs.includes(href), 'Bad category destination: ' + href);
  assert.ok(catalog.includes('data-filter="' + hub.category + '"'), 'Missing working catalog category button');
}
assert.ok(!nav[0].includes('/shop/'), 'Shop buttons must not navigate to editorial overviews');
assert.ok(!catalog.includes('aria-label="Browse dedicated PUBG Mobile categories"'), 'Obsolete editorial links still displayed');
assert.ok(home.includes('/assets/category-nav.css') && catalog.includes('/assets/category-nav.css'), 'Missing category design');
assert.ok(catalog.includes("currentCategory = urlParams.get('category')"), 'Catalog should read deep-link category');
assert.ok(catalog.includes("allProducts.filter(p => p.category === currentCategory)"), 'Catalog must filter actual products');
console.log('Passed: 6 category shopping links, selected filter destinations and premium styling.');
