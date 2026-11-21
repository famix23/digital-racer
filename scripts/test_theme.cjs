"use strict";
/* Check real built pages and reusable theme/launch components without third-party modules. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const read = p => fs.readFileSync(path.join(root,p), "utf8");
const stylesheet = read("assets/theme.css");
const script = read("assets/theme.js");
const home = read("index.html");
const studio = read("dropzone/index.html");
const source = read("scripts/build_seo.py");
new vm.Script(script, {filename:"theme.js"});
assert.ok(stylesheet.includes('html[data-dr-theme="light"]'),'Missing light theme overrides');
assert.ok(stylesheet.includes('.dr-event-feature') && stylesheet.includes('.dr-studio-feature'),'Missing launch design');
assert.ok(stylesheet.includes('@media(max-width:700px)'), 'Banner must adapt on phones');
assert.ok(script.includes("localStorage.setItem(KEY, mode)"), 'Theme choice must persist');
assert.ok(script.includes('button.setAttribute("aria-pressed"'), 'Theme toggle must expose selected appearance');
assert.ok(script.includes('document.createElement("button")'), 'Theme toggle must be keyboard-operable');
assert.ok(source.includes("THEME_HEAD") && source.includes('document.documentElement.setAttribute("data-dr-theme",theme)'),
  'Build must support theme before first paint');

function checkHTML(p) {
  const html=read(p);
  assert.equal(html.split('href="/assets/theme.css"').length-1,1,p+" must contain one theme stylesheet");
  assert.equal(html.split('src="/assets/theme.js"').length-1,1,p+" must contain one theme script");
  assert.ok(html.includes('data-dr-theme'),p+" must bootstrap before paint");
  return html;
}
for (const page of ["index.html","catalog.html","product.html","blog/index.html","about/index.html",
  "contact/index.html","privacy/index.html","terms/index.html","guides/index.html",
  "guides/pubg-mobile-account-safety/index.html","guides/pubg-mobile-skins-explained/index.html",
  "shop/pubg-mobile-car-cards/index.html","dropzone/index.html","404.html"]) checkHTML(page);
const manifest=JSON.parse(read("p/index.json"));
assert.ok(manifest.length>700,'Expected full product inventory');
for (const p of manifest) checkHTML(p.url.slice(1)+"index.html");
const sampleBlog=read("content/blog-search-titles.json");
for(const slug of Object.keys(JSON.parse(sampleBlog)).slice(0,3))checkHTML("blog/"+slug+"/index.html");
const shopHubs=JSON.parse(read("content/shop-hubs.json"));
for(const h of shopHubs)checkHTML("shop/"+h.slug+"/index.html");

assert.ok(home.includes('class="dr-event-feature"') && home.includes("NOV 20, 2026"),'Live Bentley banner missing');
assert.ok(home.includes('/catalog?category=Car%20Card&amp;search=Bentley'),'Bentley banner must lead to real Bentley products');
assert.ok(home.includes('href="/dropzone/?brand=Bentley"'),'Bentley feature must deep-link to Speed Drift');
assert.ok(home.includes('class="dr-studio-feature"'),'Speed Drift homepage feature missing');
assert.ok(studio.includes('name="robots" content="noindex'),'Payment UI must remain excluded from indexing');
assert.ok(studio.includes('src="/dropzone/payment-config.js"'),'Payment settings must remain intact');
assert.ok(studio.includes('id="sample" hidden'),'Example UID must not be suggested to real buyers');
console.log("Theme + event checks passed: dark/light preference across "+manifest.length+
  " product pages, 6 shopping hubs, editorial pages and payment studio.");

