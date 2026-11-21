/* Prevent design regressions without depending on a GUI browser or font service. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname,'..');
const read = p => fs.readFileSync(path.join(root,p),'utf8');
const home=read('index.html');
const catalog=read('catalog.html');
const helper=read('assets/storefront.js');
const css=read('assets/storefront-polish.css');
const shopTemplate=read('scripts/shop_template.html.txt');
const hubs=JSON.parse(read('content/shop-hubs.json'));
const inventoryRaw=JSON.parse(read('inventory.json'));
const inventory=Array.isArray(inventoryRaw)?inventoryRaw:inventoryRaw.items;
const manifest=JSON.parse(read('p/index.json'));
for(const [name,markup] of [['home',home],['catalog',catalog]]){
 assert.ok(markup.includes('<link rel="stylesheet" href="/assets/storefront-polish.css">'),name+': polish CSS missing');
 assert.ok(markup.includes('href="/assets/mobile-shopping.css"'),name+': mobile CSS missing');
}
assert.ok(helper.includes("window.location.pathname"),'Product CSS must be scoped to product routes');
assert.ok(helper.includes("style.href = '/assets/mobile-shopping.css'"),'Product mobile CSS lost');
assert.ok(helper.includes("polish.href = '/assets/storefront-polish.css'"),'Product design CSS lost');
assert.ok(css.includes('@media(min-width:851px)'), 'Desktop layout styles missing');
assert.ok(css.includes('@media(max-width:600px)'), 'Phone layout styles missing');
assert.ok(css.includes('@media(max-width:350px)'), 'Narrow phone layout missing');
assert.ok(css.includes('prefers-reduced-motion'), 'Reduced-motion support missing');
assert.ok(css.includes('pointer:coarse'), 'Avoid animated hover on touch screens');
assert.ok(css.includes('body>header .hero-ctas{display:none;}'), 'Do not reintroduce duplicate category buttons');
assert.ok(css.includes('.dr-shop-categories{margin-bottom:0!important;'), 'No oversized gap above products');
assert.ok(css.includes('.main-wrapper .whatsapp-btn'), 'Product purchase controls must be styled');
assert.ok(css.includes('.catalog-container .sort-select'), 'Catalog controls must stay legible');
assert.ok(css.includes('.dr-category-page .product-card'), 'Editorial hubs need product-card polish');
assert.ok(shopTemplate.includes('href="/assets/storefront-polish.css"'), 'Future shop pages must use same CSS');
assert.ok(shopTemplate.includes('body class="dr-category-page"'), 'Scoped shop page class missing');
assert.ok(!shopTemplate.includes('href="/shop/%%'), 'No shopping button should open a blog');
for(const hub of hubs){
 const page=read('shop/'+hub.slug+'/index.html');
 assert.ok(page.includes('href="/assets/storefront-polish.css"'),'Static hub CSS missing: '+hub.slug);
 assert.ok(page.includes('body class="dr-category-page"'),'Static hub class missing: '+hub.slug);
 assert.ok(page.indexOf('<section class="listing-head">') < page.indexOf('<details class="detail dr-buying-advice">'),
   'Product cards must precede long buying guide: '+hub.slug);
 const cards=(page.match(/class="product-card" href="/g)||[]).length;
 assert.ok(cards>0 && cards<=12,'Hub must display real product examples: '+hub.slug);
}
assert.equal(manifest.length,inventory.length,'Product count changed during design polish');
const staticCatalog=catalog.split('<!-- SEO:GRID:catalog:BEGIN -->')[1].split('<!-- SEO:GRID:catalog:END -->')[0];
assert.equal((staticCatalog.match(/class="product-card item-card"/g)||[]).length,Math.min(inventory.length,24),
  'Keep 24 useful server-rendered cards instead of making mobile parse the full inventory');
assert.ok(catalog.includes('class="catalog-directory-links"'),'Crawlable links to full category directories missing');
// Lightweight CSS structure check; catches accidental truncation or misplaced braces.
let depth=0;
for(const c of css){if(c==='{')depth++;if(c==='}')depth--;assert.ok(depth>=0,'Stray closing CSS brace');}
assert.equal(depth,0,'Unbalanced stylesheet');
console.log('Passed visual polish regressions: desktop + phone layouts, six product-first category hubs, and '+inventory.length+' original products.');
