"use strict";
/* Product-page marketplace enhancement must preserve existing technical SEO. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const read=p=>fs.readFileSync(path.join(root,p),"utf8");
const code=read("assets/product-discovery.js");
const css=read("assets/theme.css");
const loader=read("assets/theme.js");
const sandbox={window:{}};
vm.runInNewContext(code,sandbox,{filename:"product-discovery.js"});
const recommend=sandbox.window.DRProductDiscoveryRank;
assert.equal(typeof recommend,"function","Expose deterministic recommendation ranking");
const feed=JSON.parse(read("assets/catalog-index.json"));
assert.ok(feed.length>900,"Full inventory feed must remain available");
const target=feed.find(x=>x.url==="/p/bentley-prismatic-suv-car-card-pubg-mobile-bentayga-azure/");
assert.ok(target,"Use an actual existing Bentley product listing");
const before=JSON.stringify(feed);
const ranked=recommend(target,feed,160);
assert.ok(ranked.length>70,"Must suggest multiple other real product pages");
assert.ok(ranked.slice(0,8).every(x=>x.category==="Car Card" &&
  /bentley/i.test(x.title)),"Other genuine Bentley car cards should rank first");
assert.ok(ranked.some(x=>x.category==="Car Card" && !/bentley/i.test(x.title)),
  "Reach beyond Bentley into other real car-card brands");
assert.ok(ranked.every(x=>/^\/p\/[a-z0-9-]+\/$/.test(x.url)),"Only real indexed product URL shapes");
assert.ok(!ranked.some(x=>x.url===target.url),"Never recommend the currently viewed item");
assert.equal(new Set(ranked.map(x=>x.url)).size,ranked.length,"No duplicate recommendations");
assert.deepEqual(ranked.map(x=>x.url),recommend(target,feed,160).map(x=>x.url),
  "Recommendations must be deterministic");
assert.equal(JSON.stringify(feed),before,"Recommendation logic must never mutate the catalog");
const acc=feed.find(x=>x.category==="Account");
const accountMatches=recommend(acc,feed,12);
assert.ok(accountMatches.every(x=>x.category==="Account"),"Account discovery should prioritize accounts");
const uc=feed.find(x=>x.category==="UC Top-Up");
assert.ok(recommend(uc,feed,10).every(x=>x.category==="UC Top-Up"),"UC page should prioritize UC top-ups");
const wrong=recommend(target,[{title:"Fake",category:"Car Card",url:"javascript:alert(1)",price:"99"}],6);
assert.equal(wrong.length,0,"Never create unsafe product links");

for(const p of ["product.html","p/bentley-prismatic-suv-car-card-pubg-mobile-bentayga-azure/index.html"]){
  const html=read(p);
  assert.ok(html.includes('rel="canonical"'),p+" retains canonical metadata");
  if (p.startsWith("p/")) assert.ok(html.includes('application/ld+json'),p+" retains structured data");
  assert.ok(html.includes('id="buy-btn"'),p+" retains the WhatsApp purchase CTA");
  assert.ok(html.includes('id="related-grid"'),p+" keeps original crawlable related links");
  assert.ok(html.includes('src="/assets/theme.js" defer'),p+" gets enhancement through existing global script");
}
const bentleyHtml=read("p/bentley-prismatic-suv-car-card-pubg-mobile-bentayga-azure/index.html");
const staticRelated=[...bentleyHtml.matchAll(/<a href="(\/p\/[^"]+\/)" class="rel-card">/g)];
assert.equal(staticRelated.length,4,"Four static, crawlable related links must be retained unchanged");
assert.ok(staticRelated.every(m=>m[1]!==target.url),"No self link among static related items");
assert.ok(code.includes('fetch("/assets/catalog-index.json"'),"Use existing compact catalog feed, not another inventory API");
assert.ok(!code.includes("inventory.json")&&!code.includes("/p/index.json"),"Do not add heavyweight fetches");
assert.ok(!code.includes("innerHTML =")&&!code.includes("document.title ="),"Do not rewrite original product details or SEO title");
assert.ok(loader.includes('script.src = "/assets/product-discovery.js"'),"Product-page enhancement loader required");
assert.ok(loader.includes('document.querySelector(".product-grid-layout")'),"Do not load discovery code on homepage/catalog");
assert.ok(css.includes("grid-template-columns:minmax(190px,235px) minmax(0,1fr) minmax(295px,355px)"),
  "Wide desktop requires 3-column marketplace layout");
assert.ok(css.includes("@media(max-width:900px)")&&css.includes(".dr-discovery-rail{display:none}"),
  "Mobile must prioritize product images and price, not introduce a sidebar");
assert.ok(css.includes('html[data-dr-theme="light"] .dr-discovery-rail'),
  "Keep discovery links readable in light theme");
console.log("Product discovery checks passed:",feed.length,"real listings; same-brand, car-card, UC and account ranking; 4 SEO static related links preserved.");
