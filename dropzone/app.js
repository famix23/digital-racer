/* DigitalRacer Speed Drift: frontend-only demonstration. No network writes, payments or game API. */
(function(){
"use strict";
var all=Array.isArray(window.DROPZONE_CARS)?window.DROPZONE_CARS:[];
var state={brand:"All",search:"",limit:12,selected:null,qty:1,recipient:null,txHash:"",screen:1};
var payment=window.SPEED_DRIFT_PAYMENT||{};
var brandImages=window.SPEED_DRIFT_BRAND_IMAGES||{};
var unitUSD=Number(payment.unitPriceUSD)||120;
var unitUSDT=Number(payment.unitPriceUSDT)||120;
function totalUSD(){return "$"+(state.qty*unitUSD).toFixed(2)}
function totalUSDT(){return (state.qty*unitUSDT).toFixed(2)+" USDT"}
var $=function(id){return document.getElementById(id)};
var palette={Bentley:"#766a4c",Lamborghini:"#756129",Ferrari:"#763327",Bugatti:"#34556a",Pagani:"#4c5976",Dodge:"#634133",McLaren:"#895c33",Porsche:"#4b5267",Koenigsegg:"#3b6d72","Aston Martin":"#476555"};
var carSVG='<svg viewBox="0 0 330 140" aria-hidden="true" focusable="false"><defs><linearGradient id="dz-car-body" x2="0" y2="1"><stop stop-color="#f4e8c4"/><stop offset=".35" stop-color="#8b9299"/><stop offset=".75" stop-color="#242c3a"/><stop offset="1" stop-color="#0d1018"/></linearGradient></defs><ellipse cx="160" cy="120" rx="139" ry="8" fill="#08080a" opacity=".6"/><path d="M29 88Q43 72 78 67L117 59 139 36Q154 26 181 27L226 34Q242 38 265 65L290 72Q311 78 309 95L305 106H26L25 94Z" fill="url(#dz-car-body)" stroke="#d4cab1" stroke-width="1.1"/><path d="M125 60L149 38Q161 32 181 33L212 38 232 61Z" fill="#20364e" stroke="#8798a5" stroke-width="1"/><path d="M234 40Q251 49 258 64L237 63Z" fill="#15293c"/><path d="M43 77L107 68 100 85 33 91Z" fill="#f7eec6" opacity=".9"/><path d="M264 76L297 81 303 92 268 90Z" fill="#e6b653"/><path d="M38 98H306" stroke="#bbc8d3" stroke-width="2" opacity=".65"/><circle cx="93" cy="103" r="20" fill="#0c1017" stroke="#a8a3a0" stroke-width="4"/><circle cx="93" cy="103" r="9" fill="#818b96"/><circle cx="256" cy="103" r="20" fill="#0c1017" stroke="#a8a3a0" stroke-width="4"/><circle cx="256" cy="103" r="9" fill="#818b96"/></svg>';
function text(id,value){var el=$(id);if(el)el.textContent=String(value)}
function chip(label){var b=document.createElement("button");b.className="filter";b.type="button";b.textContent=label;b.setAttribute("aria-pressed",String(state.brand===label));b.addEventListener("click",function(){state.brand=label;state.limit=12;renderFilters();renderVehicles()});return b}
function renderFilters(){var area=$("filters");area.replaceChildren();["All","Bentley","Lamborghini","Ferrari","Bugatti","Pagani","Dodge","McLaren","Porsche","Koenigsegg","Aston Martin"].forEach(function(b){area.append(chip(b))})}
function safePhoto(path){return typeof path==="string"&&path.indexOf("/images/")===0&&!path.includes("..")&&!path.includes("\\")&&!path.includes("//")?path:""}
function visual(car,cls){
var container=document.createElement("div");
container.className=cls||"vehvisual";
container.style.setProperty("--shade",palette[car.brand]||"#5f583d");
var src=safePhoto(car.image),backup=safePhoto(brandImages[car.brand]||"");
function putPhoto(path){
  if(!path){container.insertAdjacentHTML("afterbegin",carSVG);return;}
  var img=document.createElement("img");
  img.src=path;img.loading="lazy";img.decoding="async";
  img.alt=car.brand+" vehicle skin catalogue reference";
  img.addEventListener("error",function(){
    container.replaceChildren();
    if(backup&&path!==backup)putPhoto(backup);
    else container.insertAdjacentHTML("afterbegin",carSVG);
  },{once:true});
  container.append(img);
}
putPhoto(src||backup);
return container;
}
function displayLabel(car){return car.brand+" "+car.model}
function renderVehicles(){
var filtered=all.filter(function(c){return(state.brand==="All"||state.brand===c.brand)&&((c.brand+" "+c.model+" "+c.finish).toLowerCase().includes(state.search))});
var area=$("vehicles");area.replaceChildren();var slice=filtered.slice(0,state.limit);
slice.forEach(function(car){var btn=document.createElement("button");btn.type="button";btn.className="vehicle";btn.setAttribute("aria-pressed",String(state.selected&&state.selected.id===car.id));btn.setAttribute("aria-label","Select "+displayLabel(car)+" "+car.finish);var vis=visual(car,"vehvisual");
var badge=document.createElement("span");badge.className="vehiclebadge";badge.textContent=car.brand.toUpperCase();vis.append(badge);
var tick=document.createElement("span");tick.className="check";tick.textContent="✓";vis.append(tick);btn.append(vis);
var info=document.createElement("div");info.className="vehbody";var h=document.createElement("h3");h.textContent=car.model;info.append(h);var p=document.createElement("p");p.className="finish";p.textContent=car.finish;info.append(p);var t=document.createElement("span");t.className="type";t.textContent=car.type;info.append(t);var cat=document.createElement("span");cat.className="category";cat.textContent=car.origin==="official"?"COLLAB ARCHIVE":car.origin==="store"?"STORE EXAMPLE":"CONCEPT";info.append(cat);var price=document.createElement("div");price.className="vehicleprice";price.textContent="$"+unitUSD.toFixed(2)+" / Card";info.append(price);btn.append(info);
btn.addEventListener("click",function(){select(car)});area.append(btn)});
text("resultCount",filtered.length+" vehicle finishes");$("empty").hidden=filtered.length!==0;$("more").hidden=state.limit>=filtered.length;
}
function select(car){state.selected=car;text("selected",displayLabel(car)+" — "+car.finish);$("next1").disabled=false;renderVehicles();document.querySelectorAll(".galleryitem").forEach(function(el){el.setAttribute("aria-pressed","false")})}
function step(n,fromHistory){
if(n>1&&!state.selected)n=1;
if(n>2&&!state.recipient)n=2;
n=Math.max(1,Math.min(5,n));
state.screen=n;
Array.prototype.forEach.call(document.querySelectorAll(".stage"),function(el){el.hidden=el.id!=="stage-"+n});
for(var i=1;i<=3;i++){var element=$("step-"+i),active=i===Math.min(n,3);element.classList.toggle("active",active);element.classList.toggle("done",i<Math.min(3,n));element.setAttribute("aria-current",active?"step":"false")}
if(!fromHistory&&window.history&&window.history.pushState){window.history.pushState({speedDriftStep:n},"","#step-"+n)}
window.scrollTo({top:0,behavior:"smooth"});
}
function showPreview(id){var root=$(id);root.replaceChildren();if(!state.selected)return;var vis=visual(state.selected,"minicar");root.append(vis);var body=document.createElement("div"),h=document.createElement("h3"),p=document.createElement("p");h.textContent=displayLabel(state.selected);p.textContent=state.selected.finish+" · "+state.qty+" Car Card(s) · "+totalUSD();body.append(h,p);root.append(body)}
function qty(n){state.qty=Math.max(1,Math.min(10,n));text("qtyValue",state.qty);text("detailTotal",totalUSD());showPreview("detailPreview")}
function valid(){var uid=$("uid").value.trim(),name=$("nickname").value.trim(),server=$("server").value,region=$("region").value;if(!/^[0-9]{6,20}$/.test(uid))return"Enter a numeric Player UID (6–20 digits) for the demonstration.";if(!name)return"Enter a character nickname.";if(!server||!region)return"Choose both server and country/region.";state.recipient={uid:uid,name:name,server:server,region:region};return""}
function review(){
var err=valid();text("formError",err);if(err)return;
showPreview("reviewPreview");text("r-uid",state.recipient.uid);text("r-nick",state.recipient.name);text("r-server",state.recipient.server);text("r-region",state.recipient.region);text("r-qty",state.qty+" card(s)");
text("r-item",displayLabel(state.selected)+" — "+state.selected.finish);
text("reviewTotal",totalUSD());
step(3);
}
function orderMessage(includeTx){
var parts=[
"Hello DigitalRacer — Speed Drift Car Card order",
"Vehicle: "+displayLabel(state.selected)+" — "+state.selected.finish,
"Quantity: "+state.qty+" Car Card(s)",
"Price per card: $"+unitUSD.toFixed(2),
"Order total: "+totalUSD()+" / "+totalUSDT(),
"Player UID: "+state.recipient.uid,
"Character name: "+state.recipient.name,
"Server: "+state.recipient.server,
"Region: "+state.recipient.region
];
if(includeTx){
parts.push("Network: "+payment.network);
parts.push("Receiving wallet: "+payment.walletAddress);
parts.push("Transaction hash: "+state.txHash);
parts.push("Please verify my USDT TRC20 transaction and confirm next steps.");
}else parts.push("Please confirm availability and the exact USDT TRC20 amount before payment.");
return "https://wa.me/"+(payment.supportNumber||"923454342911")+"?text="+encodeURIComponent(parts.join("\n"));
}
function openExternal(url){
var external=window.open(url,"_blank","noopener,noreferrer");
if(!external){window.location.href=url}
}
function showPayment(){
showPreview("paymentPreview");
text("paymentTotal",totalUSDT());
text("paymentUSD",totalUSD());
text("paymentNetwork",payment.network||"Network not configured");
$("walletAddress").value=payment.walletAddress||"";
$("txHash").value=state.txHash||"";
text("copyMessage","Use only "+(payment.network||"the specified network")+". Confirm the exact amount before payment.");
text("paymentError","");
step(4);
}
function verifyRequest(){
var hash=$("txHash").value.trim();
if(!/^[a-fA-F0-9]{64}$/.test(hash)){
text("paymentError","Enter your 64-character TRON TXID, or request the exact amount before paying.");
$("txHash").focus();return;
}
if(!/^T[1-9A-HJ-NP-Za-km-z]{33}$/.test(payment.walletAddress||"")){
text("paymentError","Receiving address is unavailable. Contact DigitalRacer first.");return;
}
state.txHash=hash;
text("paymentError","");
showPreview("statusPreview");
text("receiptRef","SD-"+String(Date.now()).slice(-10));
text("receiptItem",displayLabel(state.selected)+" — "+state.selected.finish);
text("receiptQty",state.qty+" Card(s)");
text("receiptTotal",totalUSD()+" / "+totalUSDT());
text("receiptPlayer",state.recipient.name+" · "+state.recipient.uid);
text("receiptServer",state.recipient.server+" / "+state.recipient.region);
text("receiptHash",hash);
text("receiptDate",new Date().toLocaleString());
$("sendDetailsLink").href=orderMessage(true);
step(5);
}
function copyWallet(){
var address=String(payment.walletAddress||"");
if(!address){text("copyMessage","Receiving address is not configured.");return}
function done(ok){text("copyMessage",ok?"Wallet address copied. Double-check network and amount.":"Copy unavailable: select and copy the address manually.")}
function fallback(){
$("walletAddress").focus();$("walletAddress").select();
var okay=false;try{okay=!!document.execCommand("copy")}catch(e){}
done(okay);
}
if(window.navigator.clipboard&&window.navigator.clipboard.writeText){
window.navigator.clipboard.writeText(address).then(function(){done(true)},fallback);
}else fallback();
}
function reset(){
state.selected=null;state.qty=1;state.recipient=null;state.txHash="";
$("recipientForm").reset();$("txHash").value="";
text("qtyValue",1);text("detailTotal",totalUSD());text("formError","");text("paymentError","");
text("selected","No vehicle selected");$("next1").disabled=true;renderVehicles();step(1);
}
function galleryTile(item){
var b=document.createElement("button");b.type="button";b.className="galleryitem";b.setAttribute("aria-label","Use catalogue sample: "+item.title);
var img=document.createElement("img"),src=safePhoto(item.thumbnail||item.image||"");if(src){img.src=src;img.alt=item.title;img.loading="lazy";img.decoding="async";img.addEventListener("error",function(){img.hidden=true})}else{img.hidden=true}b.append(img);
var p=document.createElement("p");p.textContent=item.title;b.append(p);
b.addEventListener("click",function(){
var brand=["Bentley","Ferrari","Lamborghini","Bugatti","Pagani","Dodge"].find(function(x){return item.title.toLowerCase().includes(x.toLowerCase())})||"Car Card";
select({id:"inventory-"+item.title,brand:brand,model:item.title,finish:"DigitalRacer listing example",type:"Car Card",origin:"store",image:src});
$("next1").focus();
});return b
}
function loadGallery(){fetch("/inventory.json",{cache:"no-store"}).then(function(r){if(!r.ok)throw new Error("unavailable");return r.json()}).then(function(j){var rows=Array.isArray(j.items)?j.items:[];var samples=rows.filter(function(x){return x.category==="Car Card"&&/Bentley|Ferrari|Lamborghini|Bugatti|Pagani|Dodge/i.test(x.title||"")&&safePhoto(x.thumbnail||x.image||"")}).sort(function(a,b){return (a.title.includes("Bentley")?-1:0)-(b.title.includes("Bentley")?-1:0)}).slice(0,8);if(!samples.length)return;var area=$("storeGallery");area.replaceChildren();samples.forEach(function(p){area.append(galleryTile(p))});$("gallerySection").hidden=false}).catch(function(){/* Static demonstration works without inventory access. */})}
$("search").addEventListener("input",function(e){state.search=e.target.value.trim().toLowerCase();state.limit=12;renderVehicles()});
$("more").addEventListener("click",function(){state.limit+=12;renderVehicles()});
$("next1").addEventListener("click",function(){if(!state.selected)return;showPreview("detailPreview");step(2)});
$("back1").addEventListener("click",function(){step(1)});
$("back2").addEventListener("click",function(){step(2)});
$("qtyMinus").addEventListener("click",function(){qty(state.qty-1)});
$("qtyPlus").addEventListener("click",function(){qty(state.qty+1)});
$("sample").addEventListener("click",function(){$("uid").value="5123456789";$("nickname").value="DemoRider";$("server").value="Asia";$("region").value="Pakistan";text("formError","")});
$("recipientForm").addEventListener("submit",function(e){e.preventDefault();review()});
$("toPayment").addEventListener("click",showPayment);
$("backPayment").addEventListener("click",function(){step(3)});
$("backStatus").addEventListener("click",showPayment);
$("requestQuote").addEventListener("click",function(){text("paymentError","Opening WhatsApp for a price and availability quote.");openExternal(orderMessage(false))});
$("requestVerification").addEventListener("click",verifyRequest);
$("copyWallet").addEventListener("click",copyWallet);
$("restart").addEventListener("click",reset);
window.addEventListener("popstate",function(e){
var n=e.state&&Number(e.state.speedDriftStep)||1;
step(n,true);
});
window.history.replaceState({speedDriftStep:1},"",window.location.pathname+window.location.search);
renderFilters();renderVehicles();loadGallery();
})();