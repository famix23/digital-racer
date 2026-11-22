"use strict";
/* Product-first catalog layout and accessible mobile drawer regression checks. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const read=p=>fs.readFileSync(path.join(__dirname,"..",p),"utf8");
const html=read("catalog.html");
const css=read("assets/catalog-sidebar.css");
const js=read("assets/catalog-sidebar.js");
const positions=["class=\"catalog-top-bar\"","class=\"catalog-layout\"","class=\"catalog-sidebar\"","class=\"catalog-results\"","id=\"full-catalog\""];
const indices=positions.map(x=>html.indexOf(x));
assert.ok(indices.every(x=>x>=0),"Expected product-first title, sidebar and grid");
assert.ok(indices.every((x,i)=>i===0||x>indices[i-1]),"Catalog layout must include a two-column sidebar with product results");
assert.ok(html.indexOf("class=\"catalog-safety\"")>indices[2] &&
          html.indexOf("class=\"catalog-safety\"")<indices[3],
          "Buying guidance must move into the sidebar, not push products down");
for(const cls of ["catalog-whatsapp-contact","catalog-directory-links","filter-group"]) {
  const i=html.indexOf('class="'+cls+'"');
  assert.ok(i>indices[2]&&i<indices[3],cls+" must live in the sidebar");
}
assert.equal((html.match(/class="filter-btn/g)||[]).length,7,"Retain all 7 working category filters");
assert.equal((html.match(/class="catalog-directory-links"/g)||[]).length,1);
assert.equal((html.match(/href="\/shop\/pubg-mobile-[^"]+"/g)||[]).length,6,"Retain all 6 crawlable canonical category links");
assert.ok(html.includes('id="catalog-filter-open"')&&html.includes('id="catalog-filter-close"')&&html.includes('id="catalog-sidebar-backdrop"'),"Drawer needs open, close and backdrop");
assert.ok(html.includes('src="/assets/catalog-sidebar.js" defer')&&html.includes('href="/assets/catalog-sidebar.css"'),"Page must load specific lightweight layout assets");
assert.ok(css.includes("grid-template-columns:minmax(215px,240px) minmax(0,1fr)"),"Desktop must display a left rail beside product cards");
assert.ok(css.includes("@media(max-width:930px)")&&css.includes("body.catalog-filters-open .catalog-sidebar{display:block}"),"Mobile categories must open in a drawer");
assert.ok(css.includes(".catalog-results .grid")&&css.includes("repeat(2,minmax(0,1fr))"),"Phone layout should retain two product columns");
assert.ok(html.includes("<!-- SEO:GRID:catalog:BEGIN -->")&&html.includes("<!-- SEO:GRID:catalog:END -->"),"Keep SSR catalog preview");
new vm.Script(js,{filename:"catalog-sidebar.js"});

function element(name) {
  const attrs={},events={};
  return {
    name,attrs,events,hidden:false,focus(){documentMock.activeElement=this;},
    setAttribute(k,v){attrs[k]=String(v);},
    getAttribute(k){return attrs[k]||null;},
    removeAttribute(k){delete attrs[k];},
    addEventListener(k,fn){events[k]=fn;},
    hasAttribute(k){return Object.prototype.hasOwnProperty.call(attrs,k);},
    textContent:name,
  };
}
function classes(...initial) {
  const values=new Set(initial);
  return{add:x=>values.add(x),remove:x=>values.delete(x),contains:x=>values.has(x)};
}
const button=element("toggle"),close=element("close"),backdrop=element("backdrop"),selected=element("selected"),results=element("results");
let scrolled=0;
results.scrollIntoView=()=>scrolled++;
const filters=["All","Accounts","UC Top-Ups","Car Skins","Popularity","In-Game Items","Rank Boosting"].map(t=>{
  const e=element(t);e.classList=classes(t==="All"?"active":"inactive");return e;
});
const sidebar=element("sidebar");
sidebar.querySelector=()=>filters.find(x=>x.classList.contains("active"))||null;
sidebar.querySelectorAll=x=>x===".filter-btn"?filters:[close,...filters];
const body={classList:classes()};
const docEvents={};
const documentMock={
  readyState:"complete",body,activeElement:button,
  getElementById:id=>({
    "catalog-sidebar":sidebar,"catalog-filter-open":button,"catalog-filter-close":close,
    "catalog-sidebar-backdrop":backdrop,"catalog-filter-current":selected,"catalog-results":results
  })[id]||null,
  addEventListener:(name,fn)=>{docEvents[name]=fn;}
};
const mq={matches:true,addEventListener(){}};
const windowMock={matchMedia:()=>mq};
vm.runInNewContext(js,{document:documentMock,window:windowMock});
assert.equal(selected.textContent,"All","Correct initial mobile filter");
button.events.click();
assert.equal(button.getAttribute("aria-expanded"),"true","Open drawer must expose state");
assert.ok(body.classList.contains("catalog-filters-open"),"Open drawer must be visible");
assert.equal(sidebar.getAttribute("aria-modal"),"true","Open drawer needs accessible modal semantics");
docEvents.keydown({key:"Escape",preventDefault(){}});
assert.equal(button.getAttribute("aria-expanded"),"false","Escape must close the drawer");
button.events.click();
filters[0].classList.remove("active");
filters[1].classList.add("active");
filters[1].events.click();
assert.equal(selected.textContent,"Accounts","Selecting a filter should update the compact label");
assert.ok(!body.classList.contains("catalog-filters-open"),"Filter selection closes the drawer");
assert.equal(scrolled,1,"Selecting a category should take the buyer to results");
mq.matches=false;
button.events.click();
assert.ok(!body.classList.contains("catalog-filters-open"),"Desktop sidebar should not turn into a dialog");
console.log("Catalog sidebar UX passed: grid first, 7 filters, 6 canonical category links, open/close, Escape, selection, mobile results.");
