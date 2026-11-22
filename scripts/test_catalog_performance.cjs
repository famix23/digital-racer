"use strict";
/* Mobile catalog performance, canonical discovery and progressive browsing regression. */
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const root=path.resolve(__dirname,"..");
const read=x=>fs.readFileSync(path.join(root,x),"utf8");
const html=read("catalog.html");
const manifest=JSON.parse(read("p/index.json"));
const inventoryRaw=read("inventory.json");
const inventoryJSON=JSON.parse(inventoryRaw);
const inventory=Array.isArray(inventoryJSON)?inventoryJSON:inventoryJSON.items;
const feedRaw=read("assets/catalog-index.json");
const feed=JSON.parse(feedRaw);
const searchRaw=read("assets/catalog-search.json");
const descriptions=JSON.parse(searchRaw);
const preview=html.split("<!-- SEO:GRID:catalog:BEGIN -->")[1]?.split("<!-- SEO:GRID:catalog:END -->")[0];
assert.ok(preview,"Static preview markers missing");
const staticCards=[...preview.matchAll(/<a href="(\/p\/[^"]+\/)" class="product-card item-card"/g)].map(x=>x[1]);
const count=Math.min(24,inventory.length);
assert.equal(staticCards.length,count,"Initial HTML must render only 24 recent products");
assert.equal(feed.length,inventory.length,"Compact feed missing inventory items");
assert.equal(descriptions.length,inventory.length,"Description lookup not synchronized");
assert.equal(manifest.length,inventory.length,"Manifest mismatch");
const indexed=new Map(manifest.map(x=>[x.url,x]));
for(let i=0;i<feed.length;i++){
  const p=feed[i], original=inventory[inventory.length-1-i];
  const canonical=manifest[manifest.length-1-i];
  assert.equal(p.url,canonical.url,"Unexpected canonical order");
  assert.equal(p.category,original.category,"Category changed");
  assert.equal(Number(p.price),Number(original.price),"Price changed");
  assert.ok(p.title && typeof p.title==="string","Supplier listing title missing");
  assert.ok(!p.url.includes("?") && p.url.startsWith("/p/"),"Canonical URL required");
  assert.equal(descriptions[i],original.description||"","Search content must equal supplier text");
  assert.ok(!p.thumbnail || p.thumbnail.startsWith("/images/")||p.thumbnail.startsWith("https://"),"Invalid image route");
}
assert.deepEqual(staticCards,feed.slice(0,count).map(p=>p.url),"Initial HTML must show newest real products");
const staticBuyLinks=[...preview.matchAll(/<a class="dr-card-whatsapp" href="(https:\/\/wa\.me\/923454342911\?text=[^"]+)"/g)].map(x=>x[1]);
assert.equal(staticBuyLinks.length,count,"Every first-screen catalog card needs its own WhatsApp enquiry");
for(let i=0;i<count;i++){
  const message=new URL(staticBuyLinks[i]).searchParams.get("text");
  assert.ok(message.includes(feed[i].title) && message.includes(feed[i].url) &&
    message.includes("$"+feed[i].price+" USD"),"WhatsApp enquiries must identify exact product, URL and USD price");
}
assert.equal((preview.match(/class="dr-product-tile"/g)||[]).length,count,"No invalid nested links: separate detail and purchase anchors");
assert.ok(Buffer.byteLength(html,"utf8")<190000,"Catalog HTML is too large for the mobile performance budget");
assert.ok(Buffer.byteLength(feedRaw,"utf8")<Buffer.byteLength(inventoryRaw,"utf8")*.55,
  "Compact feed too large compared with old full inventory payload");
const hubs=JSON.parse(read("content/shop-hubs.json"));
assert.equal(hubs.length,6);
for(const hub of hubs)assert.ok(html.includes('href="/shop/'+hub.slug+'/"'),"Full department link missing");
const dirs=Object.fromEntries(hubs.map(h=>[h.category,read("shop/"+h.slug+"/index.html")]));
for(const item of feed)assert.ok(dirs[item.category]?.includes('href="'+item.url+'"'),"Product not crawlable in category directory: "+item.url);
assert.ok(!html.includes("fetch('/inventory.json')")&&!html.includes("fetch('/p/index.json')"),
  "Never download huge inventory and manifest for browsing");
assert.ok(html.includes("fetch('/assets/catalog-index.json')"),"Compact feed not requested");
assert.ok(html.includes("fetch('/assets/catalog-search.json')"),"On-demand descriptions missing");
assert.ok(html.includes("searchParams.set('search', query)"),"Search URL sharing removed");
assert.ok(html.includes("if (currentSort === 'oldest') result.reverse()"),"Oldest sort missing");

// Browserless runtime test with lightweight DOM primitives, no third-party package.
const inline=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)]
  .map(x=>x[1]).find(s=>s.includes("function processAndRender()"));
assert.ok(inline,"Interactive catalog script not found");
new vm.Script(inline,{filename:"catalog.html"});
class Element {
  constructor(){this.value="";this.textContent="";this.innerHTML="";this.hidden=false;this.attrs={};this.events={};this.classList={add(){},remove(){},toggle(){}};this.parentElement={scrollWidth:1,clientWidth:1,scrollLeft:0,offsetLeft:0};this.offsetLeft=0;}
  setAttribute(k,v){this.attrs[k]=String(v);}
  getAttribute(k){return this.attrs[k]??null;}
  addEventListener(k,fn){this.events[k]=fn;}
  insertAdjacentHTML(position,v){assert.equal(position,"beforeend");this.innerHTML+=v;}
  click(){this.events.click?.({target:this,preventDefault(){}});}
  change(value){this.value=value;this.events.change?.({target:this});}
}
async function scenario(search){
  const ids=Object.fromEntries(["catalog-load-wrap","catalog-load-more","full-catalog","catalog-count",
    "search-input","search-btn","sort-select","catalog-heading-prefix","catalog-heading-focus"].map(x=>[x,new Element()]));
  ids["full-catalog"].innerHTML=preview; // Model the server-rendered first 24 cards.
  const filters=["all","Account","Car Card","Popularity","UC Top-Up","In-Game Items","Rank Boosting"].map(x=>{
    const n=new Element();n.attrs["data-filter"]=x;return n;
  });
  const origin="https://www.digitalracer.store/catalog";
  const location={href:origin+search,search,pathname:"/catalog"};
  let feedLoads=0,descriptionLoads=0;
  const fetch=async p=>{
    if(p==="/assets/catalog-index.json"){feedLoads++;return{ok:true,json:async()=>feed};}
    if(p==="/assets/catalog-search.json"){descriptionLoads++;return{ok:true,json:async()=>descriptions};}
    throw new Error("Unexpected large feed requested: "+p);
  };
  const window={DR_IMAGES:{},matchMedia:()=>({matches:true}),location,
    history:{replaceState(_state,_title,uri){location.href=origin+uri.replace("/catalog","");}}};
  const document={
    getElementById:id=>ids[id]||null,
    querySelectorAll:selector=>selector===".filter-btn"?filters:[],
  };
  let catalogObserver=null;
  class FakeIntersectionObserver {
    constructor(callback, options){this.callback=callback;this.options=options;catalogObserver=this;}
    observe(target){this.target=target;}
    trigger(isIntersecting=true){this.callback([{target:this.target,isIntersecting}]);}
  }
  const ctx={window,document,fetch,URL,URLSearchParams,console,Promise,
    IntersectionObserver:FakeIntersectionObserver};
  vm.createContext(ctx);
  vm.runInContext(read("assets/storefront.js"),ctx,{filename:"storefront.js"});
  vm.runInContext(inline,ctx,{filename:"catalog.html"});
  for(let i=0;i<8;i++)await new Promise(r=>setImmediate(r));
  return {ids,filters,feedLoads,descriptionLoads:()=>descriptionLoads,
    observer:()=>catalogObserver};
}
(async()=>{
  const initial=await scenario("");
  assert.equal(initial.feedLoads,1);
  assert.equal(initial.descriptionLoads(),0,"Do not fetch detailed inventory before user searches");
  assert.equal((initial.ids["full-catalog"].innerHTML.match(/class="product-card item-card"/g)||[]).length,Math.min(24,feed.length));
  assert.equal(initial.ids["catalog-load-wrap"].hidden,false,"Show-more must be available");
  assert.equal((initial.ids["full-catalog"].innerHTML.match(/class="dr-card-whatsapp"/g)||[]).length,count,
    "Server-rendered card WhatsApp enquiries must survive hydration");
  initial.ids["catalog-load-more"].click();
  assert.equal((initial.ids["full-catalog"].innerHTML.match(/class="product-card item-card"/g)||[]).length,Math.min(48,feed.length));
  const observer=initial.observer();
  assert.ok(observer && observer.target===initial.ids["catalog-load-wrap"],
    "Progressive scroll discovery must observe the product loading control");
  observer.trigger(false); // Offscreen must not append more products.
  assert.equal((initial.ids["full-catalog"].innerHTML.match(/class="product-card item-card"/g)||[]).length,Math.min(48,feed.length));
  observer.trigger(true); // Buyer approaches the next products while scrolling.
  assert.equal((initial.ids["full-catalog"].innerHTML.match(/class="product-card item-card"/g)||[]).length,Math.min(72,feed.length),
    "Scrolling near the end should reveal products without another button press");
  const query=await scenario("?category=Car%20Card&search=Bentley");
  assert.equal(query.feedLoads,1,"One compact initial feed");
  assert.equal(query.descriptionLoads(),1,"Fetch descriptions only for keyword searches");
  const markup=query.ids["full-catalog"].innerHTML;
  assert.ok(markup.includes("Bentley"),"Bentley deep link should reveal Bentley products");
  const categories=[...markup.matchAll(/class="product-card item-card" data-category="([^"]+)"/g)].map(x=>x[1]);
  assert.ok(categories.length && categories.every(x=>x==="Car Card"),"Deep-linked filter must apply");
  console.log("Passed mobile catalog: "+inventory.length+" products, "+staticCards.length+
    " initial cards, "+Buffer.byteLength(html,"utf8")+" HTML bytes, "+Buffer.byteLength(feedRaw,"utf8")+
    " feed bytes, searchable Bentley deep links and working show-more.");
})().catch(e=>{console.error(e);process.exitCode=1;});

