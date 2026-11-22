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
const bentleyHub = read('shop/pubg-mobile-car-cards/index.html');
assert.ok(home.includes('class="dr-event-primary" href="/shop/pubg-mobile-car-cards/"'), 'Bentley launch banner must lead to its canonical, indexable shop hub, not a JS search URL');
assert.ok(bentleyHub.includes('November 20, 2026') && bentleyHub.includes('January 12, 2027'), 'Bentley event dates must be visible to international buyers');
assert.ok(bentleyHub.includes('rel="canonical" href="https://www.digitalracer.store/shop/pubg-mobile-car-cards/"'), 'Bentley shopping hub must retain its self-canonical');
const bentleyFeatured = (bentleyHub.split('<div class="cards">')[1] || '').split('</div>')[0];
const featuredCardTitles = [...bentleyFeatured.matchAll(/<strong>([^<]+)<\/strong>/g)].map(m => m[1]);
assert.equal(featuredCardTitles.length, 12, 'Keep twelve fast, real Bentley product cards visible without JS');
assert.ok(featuredCardTitles.every(t => /bentley/i.test(t)), 'Promoted hub must prioritize Bentley skins over other vehicle brands');
// Every buyer-facing funnel must have a direct WhatsApp option; no checkout steps required.
const waNumber = 'https://wa.me/923454342911?text=';
assert.ok(home.includes('class="dr-event-secondary dr-whatsapp-conversion" href="' + waNumber), 'Bentley hero must offer immediate WhatsApp contact');
assert.ok(home.includes('keeping crawlable product cards.'), 'Homepage must preserve SSR sales links if inventory request fails');
assert.ok(catalog.includes('class="catalog-whatsapp-contact"') && catalog.includes(waNumber), 'Catalog must offer direct WhatsApp buying');
assert.ok(read('dropzone/index.html').includes('Chat on WhatsApp before payment') && read('dropzone/index.html').includes(waNumber), 'Speed Drift must offer WhatsApp before payment steps');
for (const hub of hubs) {
  const page = read('shop/' + hub.slug + '/index.html');
  assert.ok(page.includes('class="cta wa-shop-cta" href="' + waNumber), 'Missing direct WhatsApp button on ' + hub.slug);
  assert.ok(page.includes('href="/catalog?category=' + encodeURIComponent(hub.category) + '"'), 'Keep original shop browsing link on ' + hub.slug);
}
// Buyers can enquire directly from every homepage product preview, not only the floating button.
const homeProductPreviews=[...home.matchAll(/<div class="dr-product-tile"><a href="\/p\//g)];
const homeProductWhatsApp=[...home.matchAll(/class="dr-card-whatsapp" href="https:\/\/wa\.me\/923454342911\?text=/g)];
assert.equal(homeProductPreviews.length,homeProductWhatsApp.length,'Homepage preview needs one WhatsApp purchase route per product');
assert.ok(homeProductPreviews.length >= 20,'Keep all original homepage product previews accessible');
console.log('Passed: 6 category links, crawlable landing pages and direct WhatsApp sales CTAs.');
