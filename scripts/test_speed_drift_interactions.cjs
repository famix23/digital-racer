"use strict";
/* Runtime smoke tests for core Speed Drift buttons without browser dependencies. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const read=x=>fs.readFileSync(path.join(root,x),"utf8");
const html=read("dropzone/index.html");
const ids=[...new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]))];
class Element{
 constructor(tag="div"){this.tag=tag;this.events={};this.children=[];this.attrs={};this.hidden=false;this.disabled=false;this.value="";this.textContent="";this.className="";this.src="";this.style={setProperty:()=>{}};this.classes=new Set();this.classList={toggle:(name,on)=>{if(on===undefined)on=!this.classes.has(name);if(on)this.classes.add(name);else this.classes.delete(name);return on;},add:name=>this.classes.add(name),remove:name=>this.classes.delete(name)}}
 append(...children){this.children.push(...children)}
 replaceChildren(...children){this.children=[...children]}
 appendChild(child){this.children.push(child);return child}
 insertAdjacentHTML(_position,html){this.html=(this.html||"")+html}
 addEventListener(type,callback){(this.events[type]??=[]).push(callback)}
 setAttribute(name,value){this.attrs[name]=String(value)}
 getAttribute(name){return this.attrs[name]??null}
 focus(){this.focused=true}
 scrollIntoView(options){this.scrolled=true;this.scrollOptions=options}
 select(){this.selected=true}
 querySelector(_sel){return new Element()}
 click(){for(const fn of this.events.click||[])fn({target:this,preventDefault(){}})}
 fire(type,payload={}){for(const fn of this.events[type]||[])fn({target:this,preventDefault(){},...payload})}
}
const elements=Object.fromEntries(ids.map(id=>[id,new Element()]));
elements.recipientForm.reset=function(){for(const field of ["uid","nickname","server","region"])elements[field].value="";};
for(const id of ids){
  elements[id].id=id;
  const marker=new RegExp('<[^>]+\\bid="'+id+'"[^>]*>','i').exec(html)?.[0]||"";
  elements[id].disabled=/\bdisabled\b/i.test(marker);
  elements[id].hidden=/\bhidden\b/i.test(marker);
}
const document={
 createElement:tag=>new Element(tag),
 getElementById:id=>elements[id]||null,
 querySelectorAll:selector=>{
  if(selector===".stage")return [1,2,3,4,5].map(n=>elements["stage-"+n]);
  if(selector===".galleryitem")return elements.storeGallery.children;
  return [];
 },
 execCommand:()=>true
};
const history={stack:[],replaceState(s){this.stack=[s]},pushState(s){this.stack.push(s)}};
const external=[];
const window={
 history,location:{pathname:"/dropzone/",search:"",href:"/dropzone/"},
 scrollTo(){},
 addEventListener(){},
 open(url){external.push(url);return {}},
 navigator:{clipboard:{writeText:()=>Promise.resolve()}},
};
const context={window,document,navigator:window.navigator,fetch:()=>({then(first){const data=first({ok:true,json:()=>JSON.parse(read("inventory.json"))});return {then(second){second(data);return {catch:()=>{}}}}}}),console,Date,Promise,setTimeout,clearTimeout};
vm.createContext(context);
for(const file of ["dropzone/catalog.js","dropzone/payment-config.js","dropzone/app.js"]){
 vm.runInContext(read(file),context,{filename:file});
}
const fire=id=>{assert.ok(elements[id].events.click?.length,"Missing click handler for "+id);elements[id].click()};
const stage=n=>assert.equal(elements["stage-"+n].hidden,false,"Stage "+n+" should be visible");
assert.ok(elements.vehicles.children.length>0,"Catalog didn't render");
assert.ok(elements.filters.children.length>=8,"Brand filters didn't render");
assert.equal(elements.storeGallery.children.length,Math.min(12,JSON.parse(read("inventory.json")).items.filter(x=>x.category==="Car Card").length),"Speed Drift must show 12 real listing previews first");
assert.ok(elements.storeGallery.children.every(el=>el.events.click?.length),"Every Car Card catalog item must be clickable");
assert.equal(elements.galleryMore.hidden,false,"Show more must let buyers browse the full Car Card inventory");
fireGalleryMore=()=>elements.galleryMore.click();
fireGalleryMore();
assert.equal(elements.storeGallery.children.length,Math.min(24,JSON.parse(read("inventory.json")).items.filter(x=>x.category==="Car Card").length),"Next gallery batch must be accessible");

const carCardCount = JSON.parse(read("inventory.json")).items.filter(x=>x.category==="Car Card").length;
assert.ok(elements.catalogCount.textContent.includes(String(carCardCount)),"Display full Car Card listing count");

assert.equal(elements.next1.disabled,true,"Initially require a selected car");
elements.filters.children.find(el=>el.textContent==="Ferrari").click();
assert.ok(elements.vehicles.children.length>0,"Ferrari filter has no results");
assert.ok(elements.vehicles.children.every(b=>b.attrs["aria-label"].includes("Ferrari")),"Ferrari filter leaked other brands");
elements.search.value="no-car-with-this-name";elements.search.fire("input");
assert.equal(elements.vehicles.children.length,0,"Search should filter out all cars");
elements.search.value="";elements.search.fire("input");
const vehicle=elements.vehicles.children[0];
vehicle.click();
stage(2);
assert.ok(elements["stage-2"].scrolled,"Selecting a vehicle should scroll straight to Player Details");
assert.equal(elements["stage-2"].scrollOptions.block,"start","New stage should align at its start");
assert.equal(elements.next1.disabled,false,"Selected car didn't enable next");
fire("back1");stage(1);
assert.ok(elements["stage-1"].scrolled,"Back should return to the catalog");
const secondVehicle=elements.vehicles.children[1];
secondVehicle.click();
stage(2);
assert.ok(elements.detailPreview.children.length>0,"Selected vehicle preview should render immediately");
fire("back1");stage(1);
fire("next1");stage(2);
fire("qtyPlus");assert.equal(elements.qtyValue.textContent,"2");
assert.equal(elements.detailTotal.textContent,"$240.00","Two cards should cost $240");
fire("qtyMinus");assert.equal(elements.qtyValue.textContent,"1");
fire("sample");assert.equal(elements.uid.value,"5123456789");
elements.uid.value="invalid";
elements.recipientForm.fire("submit");
assert.ok(elements.formError.textContent.includes("numeric"),"Invalid UID should be rejected");
stage(2);
elements.uid.value="5123456789";
elements.recipientForm.fire("submit");
stage(3);
assert.equal(elements["r-uid"].textContent,"5123456789");
assert.equal(elements.reviewTotal.textContent,"$120.00","One card should cost $120");
fire("back2");stage(2);
elements.recipientForm.fire("submit");stage(3);
fire("toPayment");stage(4);
assert.equal(elements.walletAddress.value,"TF9TxdLcw1BdhVFKc3egwKHBTyis4fmPys");
assert.equal(elements.paymentTotal.textContent,"120.00 USDT");
fire("copyWallet");
elements.txHash.value="not-a-txid";
fire("requestVerification");stage(4);
assert.ok(elements.paymentError.textContent.includes("64-character"));
elements.txHash.value="a".repeat(64);
fire("requestVerification");stage(5);
assert.equal(elements.receiptHash.textContent,"a".repeat(64));
assert.equal(elements.receiptTotal.textContent,"$120.00 / 120.00 USDT");
assert.ok(elements.sendDetailsLink.href.startsWith("https://wa.me/"));
assert.ok(elements.sendDetailsLink.href.includes("5123456789"),"Merchant handover should contain UID");
fire("backStatus");stage(4);
fire("backPayment");stage(3);
fire("toPayment");stage(4);
fire("requestQuote");
assert.ok(external.some(url=>url.includes("Please%20confirm%20availability")),"Quote button should open WhatsApp");
elements.txHash.value="b".repeat(64);
fire("requestVerification");stage(5);
fire("restart");stage(1);
assert.equal(elements.next1.disabled,true,"Restart should clear selection");
assert.equal(elements.qtyValue.textContent,"1","Restart should reset quantity");

// Real storefront listing selection should carry the exact title, real listing price and photo.
// A bundle must not be silently re-priced at the $120 finish-card price.
const inventory=JSON.parse(read("inventory.json")).items.filter(x=>x.category==="Car Card");
const expensive=inventory.find(x=>Number(x.price)>500);
assert.ok(expensive,"Fixture should include an actual bundle listing with distinct pricing");
let card=elements.storeGallery.children.find(el=>el.attrs["aria-label"].includes(expensive.title));
assert.ok(card,"Actual catalog listing should be visible and selectable");
card.click();stage(2);
assert.equal(elements.detailTotal.textContent,"$"+Number(expensive.price).toFixed(2),"Selected original listing price must be preserved");
assert.ok(elements.detailPreview.children[1].children[0].textContent===expensive.title,"Use exact listing title in review");
fire("qtyPlus");
assert.equal(elements.detailTotal.textContent,"$"+(Number(expensive.price)*2).toFixed(2),"Storefront listing quantity should recalculate at its own price");
fire("back1");stage(1);
elements.catalogSearch.value="Bentley";elements.catalogSearch.fire("input");
assert.ok(elements.storeGallery.children.length>0,"Catalog search should find Bentley listings");
assert.ok(elements.storeGallery.children.every(el=>el.attrs["aria-label"].toLowerCase().includes("bentley")),"Catalog search should filter to Bentley");

console.log("Speed Drift interactions passed: mobile auto-advance on vehicle tap, scroll-to-form, brand filters, back/next, quantity, UID validation, wallet copy, TXID, WhatsApp, reset.");
