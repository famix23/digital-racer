/* Mobile UX regression checks without dependencies: preserve crawlable HTML,
   keep catalog pagination accessible, retain working deep links and responsive CSS. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root,p), 'utf8');
const home = read('index.html');
const catalog = read('catalog.html');
const css = read('assets/mobile-shopping.css');
const helper = read('assets/storefront.js');
const template = read('scripts/shop_template.html.txt');
const inventoryJson = JSON.parse(read('inventory.json'));
const inventory = Array.isArray(inventoryJson) ? inventoryJson : inventoryJson.items;
const manifest = JSON.parse(read('p/index.json'));
assert.equal(inventory.length, manifest.length, 'Catalog and product manifest must match.');
assert.ok(home.includes('/assets/mobile-shopping.css') && catalog.includes('/assets/mobile-shopping.css'), 'Mobile stylesheet missing.');
assert.ok(home.includes('class="dr-shop-categories"'), 'Category shopping shortcuts missing.');
assert.ok(css.includes('header .hero-ctas{display:none;'), 'Mobile hero duplicates must be hidden.');
assert.ok(css.includes('.dr-shop-tile{min-height:50px'), 'Category tap targets must remain generous.');
assert.ok(css.includes('body > nav'), 'Main mobile navigation must not target nested category navigation.');
assert.ok(css.includes('@media(max-width:350px)'), 'Small phone breakpoint missing.');
assert.ok(css.includes('prefers-reduced-motion'), 'Reduced-motion support missing.');
assert.ok(catalog.includes('<details class="catalog-safety"'), 'Buyer tips should be optional, not above all products.');
assert.ok(catalog.includes('<button class="catalog-load-more" id="catalog-load-more" type="button" aria-controls="full-catalog">'), 'Accessible show-more control missing.');
assert.ok(catalog.includes('catalogBatchSize = window.matchMedia'), 'Viewport-aware batch sizing missing.');
assert.ok(catalog.includes("fetch('/assets/catalog-index.json')") && catalog.includes("fetch('/assets/catalog-search.json')"), 'Compact interactive catalog feeds missing.');
assert.ok(!catalog.includes("fetch('/inventory.json')") && !catalog.includes("fetch('/p/index.json')"), 'Mobile catalog must not download full inventory or product manifest on entry.');
assert.ok(catalog.includes('class="catalog-directory-links"'), 'HTML-accessible category directories missing.');
assert.ok(catalog.includes('function appendCatalogBatch()'), 'Catalog incremental rendering missing.');
assert.ok(catalog.includes("grid.insertAdjacentHTML('beforeend'"), 'Next batch must append cards, not destroy previous cards.');
assert.ok(catalog.includes('filteredProducts = result;') && catalog.includes('renderedCount = 0;'), 'Filters must reset pagination.');
assert.ok(catalog.includes('loadWrap.hidden = renderedCount >= total;'), 'Show more must disappear when all products are shown.');
assert.ok(catalog.includes('keeping pre-rendered product cards'), 'Failed requests must not wipe crawlable catalog cards.');
const staticGrid = catalog.split('<!-- SEO:GRID:catalog:BEGIN -->')[1].split('<!-- SEO:GRID:catalog:END -->')[0];
const htmlCards = [...staticGrid.matchAll(/class="product-card item-card" data-category="([^"]+)"/g)];
assert.equal(htmlCards.length, Math.min(24, inventory.length), 'Keep a compact crawlable preview; full product URLs remain linked from category directories.');
const linksAcrossHubs = new Set();
for(const hub of JSON.parse(read('content/shop-hubs.json'))){
  const html = read('shop/'+hub.slug+'/index.html');
  for(const match of html.matchAll(/href="(\/p\/[^\"]+\/)"/g)) linksAcrossHubs.add(match[1]);
}
assert.equal(manifest.filter(p=>linksAcrossHubs.has(p.url)).length, inventory.length, 'Every listing must remain linked from crawlable shop directories.');
assert.ok(helper.includes("window.location.pathname") && helper.includes('/assets/mobile-shopping.css'), 'Generated product pages must receive progressive mobile styling.');
assert.ok(template.includes('@media(max-width:750px)') && template.includes('listing-directory'), 'Responsive category landing page missing.');
for(const entry of manifest.slice(0,2).concat(manifest.slice(-2))){
  const productHTML = read(entry.url.slice(1)+'index.html');
  assert.ok(productHTML.includes('/assets/storefront.js'), 'Generated product page must load shared mobile enhancement script.');
}
console.log('Passed mobile UX checks: responsive controls, mobile CSS, incremental catalog and all ' + inventory.length + ' crawlable product links.');
