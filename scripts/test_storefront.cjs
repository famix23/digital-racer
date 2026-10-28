/* Regression checks run without a browser or third-party packages: node scripts/test_storefront.cjs */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const sandbox = { URL, window: { DR_IMAGES: {} } };
vm.createContext(sandbox);
vm.runInContext(read('assets/storefront.js'), sandbox);
for (const unsafe of ['javascript:alert(1)', 'data:image/svg+xml,<svg>', '//evil.example/a', 'https://user:password@evil.example/a', '\\evil.example\\x', 'https://evil.example/\n']) {
  // Trailing whitespace is trimmed; embedded controls and unsafe schemes must fail.
  if (unsafe.endsWith('\n')) continue;
  assert.equal(sandbox.safeImagePath(unsafe), '', unsafe);
}
assert.equal(sandbox.safeImagePath('https://evil.example/\nx'), '');
assert.equal(sandbox.safeImagePath('images/a.jpg'), '/images/a.jpg');
assert.equal(sandbox.safeImagePath('https://example.com/a.jpg'), 'https://example.com/a.jpg');
const payload = '\"><img src=x onerror=alert(1)><script>alert(2)</script>&';
assert.ok(!sandbox.escapeHTML(payload).includes('<'));
const data = JSON.parse(read('inventory.json'));
const products = Array.isArray(data) ? data : data.items;
const manifest = JSON.parse(read('p/index.json'));
assert.equal(manifest.length, products.length);
assert.equal(new Set(products.map(p => sandbox.matchingProduct(manifest, p).url)).size, products.length,
  'Every product must resolve to its own canonical URL, including identical title/price pairs.');
for (const file of ['index.html', 'catalog.html', 'product.html']) {
  const html = read(file);
  for (const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)) {
    if (match[0].includes('application/ld+json')) { JSON.parse(match[1]); continue; }
    new vm.Script(match[1], { filename: file });
  }
  if (file !== 'product.html') {
    const card = html.match(/  function createCardHTML\(product\) \{[\s\S]*?\n  \}/)[0];
    const context = { ...sandbox, productUrl: () => '/p/test/', formatImagePath: sandbox.safeImagePath };
    vm.createContext(context);
    vm.runInContext(card, context);
    const rendered = context.createCardHTML({ title: payload, price: payload, category: payload, badge: payload, thumbnail: payload });
    assert.ok(!rendered.includes('<script>') && !rendered.includes('<img src=x'), `${file}: injected product HTML`);
  }
}
const description = read('product.html').match(/  function parseDescription\(text\) \{[\s\S]*?\n  \}/)[0];
vm.runInContext(description, sandbox);
assert.equal(sandbox.parseDescription(payload + '\n-' + payload).match(/<script>/), null);
for (const p of manifest) {
  const html = read(p.url.slice(1) + 'index.html');
  assert.ok(html.includes('https://www.digitalracer.store' + p.url));
  const blocks = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)].map(m => JSON.parse(m[1]));
  const product = blocks.find(b => b['@type'] === 'Product');
  assert.equal(Number(product.offers.price), Number(p.price));
  assert.ok(!/<meta name="robots" content="noindex/.test(html), 'Canonical product pages must stay indexable');
  assert.ok(html.includes('Buy now on whatsapp number +923454342911'));
}
console.log(`Passed: ${products.length} distinct product URLs, matching offer prices, indexable pages, injection regressions and inline JavaScript syntax.`);
