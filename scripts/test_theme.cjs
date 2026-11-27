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
assert.ok(home.includes('class="dr-event-primary" href="/shop/pubg-mobile-car-cards/"'),'Bentley banner must link directly to the canonical Bentley shopping hub');
assert.ok(home.includes('href="/dropzone/?brand=Bentley"'),'Bentley feature must deep-link to Speed Drift');
assert.ok(home.includes('class="dr-studio-feature"'),'Speed Drift homepage feature missing');
assert.ok(studio.includes('name="robots" content="noindex'),'Payment UI must remain excluded from indexing');
assert.ok(studio.includes('src="/dropzone/payment-config.js"'),'Payment settings must remain intact');
assert.ok(studio.includes('id="sample" hidden'),'Example UID must not be suggested to real buyers');
console.log("Theme + event checks passed: dark/light preference across "+manifest.length+
  " product pages, 6 shopping hubs, editorial pages and payment studio.");



/* Exercise the actual theme button with a small DOM double. */
const stored = new Map([["digitalracer-theme","light"]]);
const element = (tag) => {
  const attrs={}, events={};
  return {tag,attrs,events,innerHTML:"",appendChild(child){this.child=child;},
    addEventListener(name,fn){events[name]=fn;},
    setAttribute(name,value){attrs[name]=String(value);},
    getAttribute(name){return attrs[name]||null;},
    classList:{add(){}}
  };
};
const host=element("nav");
const themeButton=element("button");
const htmlRoot=element("html");htmlRoot.style={};
const browserBar=element("meta");
const browserEvents={};
const documentMock={
  readyState:"complete",documentElement:htmlRoot,
  addEventListener(name,fn){browserEvents[name]=fn;},
  getElementById(){return null;},
  createElement(type){assert.equal(type,"button");return themeButton;},
  querySelector(css){
    if(css==='body > nav .nav-links')return host;
    if(css==='meta[name="theme-color"]')return browserBar;
    return null;
  },
  body:element("body")
};
const windowMock={addEventListener(){}};
const storageMock={getItem:key=>stored.get(key)||null,setItem:(key,value)=>stored.set(key,value)};
vm.runInNewContext(script,{document:documentMock,window:windowMock,localStorage:storageMock,URL});
assert.equal(htmlRoot.getAttribute("data-dr-theme"),"light","Restored light theme");
assert.equal(themeButton.attrs["aria-pressed"],"true");
assert.equal(host.child,themeButton,"Navigation must own switch");
themeButton.events.click();
assert.equal(htmlRoot.getAttribute("data-dr-theme"),"dark");
assert.equal(stored.get("digitalracer-theme"),"dark","Choice must persist");
assert.equal(themeButton.attrs["aria-pressed"],"false");
assert.equal(browserBar.attrs.content,"#050505");
themeButton.events.click();
assert.equal(htmlRoot.getAttribute("data-dr-theme"),"light");
assert.equal(browserBar.attrs.content,"#f8f7f4");
// Delegated WhatsApp clicks must report only non-sensitive context to an
// already configured GA4 tag without intercepting outbound navigation.
const events=[];
const fakeCategory={textContent:"Car Card"};
const fakeDetail={getAttribute(){return "/p/sample-bentley-card/";}};
const fakeTile={querySelector(sel){return sel.startsWith("a.product-card")?fakeDetail:fakeCategory;}};
const fakeLink={
  href:"https://wa.me/923454342911?text=PRIVATE-MESSAGE-MUST-NOT-BE-SENT",
  id:"",classList:{contains(cls){return cls==="dr-card-whatsapp";}},
  closest(sel){return sel===".dr-product-tile"?fakeTile:null}
};
const fakeTarget={closest(){return fakeLink;}};
windowMock.location={href:"https://www.digitalracer.store/catalog",pathname:"/catalog"};
windowMock.gtag=(...args)=>events.push(args);
browserEvents.click({target:fakeTarget});
assert.equal(events.length,1,"An existing GA4 setup must receive a WhatsApp click");
assert.equal(events[0][0],"event");
assert.equal(events[0][1],"whatsapp_click");
assert.equal(events[0][2].click_area,"product_card");
assert.equal(events[0][2].product_path,"/p/sample-bentley-card/");
assert.equal(events[0][2].item_category,"Car Card");
assert.ok(!JSON.stringify(events).includes("PRIVATE-MESSAGE"),"Never send prefilled WhatsApp text to analytics");
delete windowMock.gtag;
browserEvents.click({target:fakeTarget});
assert.equal(events.length,1,"Absent GA4 must not throw or fabricate events");
console.log("Appearance toggle interactive tests passed.");

/* Storefront-only responsive and deep directory photo regression guards. */
assert.ok(stylesheet.includes(".dr-category-page .cta.wa-shop-cta{margin-left:0}"), "Mobile category CTA must not overflow");
assert.ok(stylesheet.includes('html[data-dr-theme="light"] .dr-category-page .dr-feature-card'), "Light-mode named collections must remain legible");
assert.ok(stylesheet.includes(".main-wrapper .desc-content table"), "Wide product description content must scroll inside its own region");
assert.ok(script.includes('fetch("/assets/catalog-index.json")') && script.includes("IntersectionObserver"), "Deep category photos must load progressively");
assert.ok(script.includes('directory.addEventListener("toggle"'), "Closed directories must not fetch product photos");
