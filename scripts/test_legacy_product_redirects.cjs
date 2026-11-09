/* Test Cloudflare legacy query URL canonicalization without network access. */
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');

async function main() {
  const root = path.resolve(__dirname, '..');
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'p/index.json'), 'utf8'));
  const { default: worker, canonicalProductRoute } = await import('../src/worker.mjs');
  const canonicalURL = value => 'https://www.digitalracer.store' + value;
  const assetCalls = [];
  const env = {
    ASSETS: {
      async fetch(request) {
        const u = new URL(request.url);
        assetCalls.push(u.pathname);
        if (u.pathname === '/p/index.json') {
          return new Response(JSON.stringify(manifest), { status: 200, headers: { 'Content-Type': 'application/json' } });
        }
        return new Response('Generic product fallback', { status: 200, headers: { 'Content-Type': 'text/html' } });
      }
    }
  };
  const get = url => worker.fetch(new Request(url), env);
  const rootURL = 'https://www.digitalracer.store';
  const titles = new Map();
  for (const entry of manifest) {
    const list = titles.get(entry.title) ?? [];
    list.push(entry);
    titles.set(entry.title, list);
  }
  let unique = 0;
  for (const [title, entries] of titles) {
    const route = canonicalProductRoute(title, manifest);
    if (entries.length > 1) {
      assert.equal(route, null, 'Ambiguous titles must not redirect');
      continue;
    }
    assert.equal(route, entries[0].url, 'Product manifest must be the source of canonical URLs');
    const r = await get(rootURL + '/product?item=' + encodeURIComponent(title));
    assert.equal(r.status, 301, title);
    assert.equal(r.headers.get('location'), canonicalURL(route), title);
    unique++;
  }
  const aliasCases = [
    ['X ULTIMATES 👑 ANUKHARA X-SUIT (⭐⭐⭐) ❄️ M416 ROARING IMMOLATION MAXX + UMP ANIVERSARRY COMBO (2x LOOT CRATE) 🏎️ LOTUS EMIRA SPORTS',
     '/p/pubg-mobile-account-anukhara-x-suit-3-m416-roaring-immolation-max/'],
    ['( Karambit ) And ( Nine-Tails ) 2 In One Deal 🔥pubg mobile card collection',
     '/p/pubg-mobile-karambit-nine-tails-card-bundle-2-in-1-deal-instant/'],
    ['Near to 98 Collection Account World Top 100 Account | Most Rarest Inventory every ||',
     '/p/pubg-mobile-world-top-100-account-near-98-collection-13-maxed-x-suits/'],
  ];
  for (const [title, route] of aliasCases) {
    assert.ok(manifest.some(row => row.url === route), 'Old title destination must exist: ' + title);
    for (const originalRoute of ['/product', '/product.html']) {
      const response = await get(rootURL + originalRoute + '?item=' + encodeURIComponent(title));
      assert.equal(response.status, 301);
      assert.equal(response.headers.get('location'), canonicalURL(route));
    }
  }
  for (const uri of ['/product', '/product.html?item=Not%20a%20real%20listing', '/catalog']) {
    const response = await get(rootURL + uri);
    assert.equal(response.status, 200, 'Unknown/non-product requests retain asset behavior');
  }
  assert.equal(canonicalProductRoute('__unknown__', manifest), null);
  assert.equal(canonicalProductRoute(manifest[0].title, [{title: manifest[0].title, url: 'https://evil.example'}]), null);
  assert.ok(assetCalls.includes('/product.html') && assetCalls.includes('/p/index.json'));
  console.log('Passed: ' + unique + ' unique canonical title redirects, 3 renamed-title aliases, safe fallbacks and no open redirects.');
}
main().catch(err => { console.error(err); process.exitCode = 1; });
