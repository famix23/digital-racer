/* DigitalRacer Speed Drift: frontend-only demonstration. No network writes, payments or game API. */
(function(){
"use strict";
var all=Array.isArray(window.DROPZONE_CARS)?window.DROPZONE_CARS:[];
var state={brand:"All",search:"",limit:12,selected:null,qty:1,recipient:null,timer:null};
var $=function(id){return document.getElementById(id)};
var palette={Bentley:"#766a4c",Lamborghini:"#756129",Ferrari:"#763327",Bugatti:"#34556a",Pagani:"#4c5976",Dodge:"#634133",McLaren:"#895c33",Porsche:"#4b5267",Koenigsegg:"#3b6d72","Aston Martin":"#476555"};
var carSVG='<svg viewBox="0 0 330 140" aria-hidden="true" focusable="false"><defs><linearGradient id="dz-car-body" x2="0" y2="1"><stop stop-color="#f4e8c4"/><stop offset=".35" stop-color="#8b9299"/><stop offset=".75" stop-color="#242c3a"/><stop offset="1" stop-color="#0d1018"/></linearGradient></defs><ellipse cx="160" cy="120" rx="139" ry="8" fill="#08080a" opacity=".6"/><path d="M29 88Q43 72 78 67L117 59 139 36Q154 26 181 27L226 34Q242 38 265 65L290 72Q311 78 309 95L305 106H26L25 94Z" fill="url(#dz-car-body)" stroke="#d4cab1" stroke-width="1.1"/><path d="M125 60L149 38Q161 32 181 33L212 38 232 61Z" fill="#20364e" stroke="#8798a5" stroke-width="1"/><path d="M234 40Q251 49 258 64L237 63Z" fill="#15293c"/><path d="M43 77L107 68 100 85 33 91Z" fill="#f7eec6" opacity=".9"/><path d="M264 76L297 81 303 92 268 90Z" fill="#e6b653"/><path d="M38 98H306" stroke="#bbc8d3" stroke-width="2" opacity=".65"/><circle cx="93" cy="103" r="20" fill="#0c1017" stroke="#a8a3a0" stroke-width="4"/><circle cx="93" cy="103" r="9" fill="#818b96"/><circle cx="256" cy="103" r="20" fill="#0c1017" stroke="#a8a3a0" stroke-width="4"/><circle cx="256" cy="103" r="9" fill="#818b96"/></svg>';
function text(id,value){var el=$(id);if(el)el.textContent=String(value)}
function chip(label){var b=document.createElement("button");b.className="filter";b.type="button";b.textContent=label;b.setAttribute("aria-pressed",String(state.brand===label));b.addEventListener("click",function(){state.brand=label;state.limit=12;renderFilters();renderVehicles()});return b}
function renderFilters(){var area=$("filters");area.replaceChildren();["All","Bentley","Lamborghini","Ferrari","Bugatti","Pagani","Dodge","McLaren","Porsche","Koenigsegg","Aston Martin"].forEach(function(b){area.append(chip(b))})}
function safePhoto(path){return typeof path==="string"&&path.indexOf("/images/")===0&&!path.includes("..")&&!path.includes("\\")&&!path.includes("//")?path:""}
function visual(car,cls){var container=document.createElement("div");container.className=cls||"vehvisual";container.style.setProperty("--shade",palette[car.brand]||"#5f583d");var src=safePhoto(car.image);if(src){var img=document.createElement("img");img.src=src;img.loading="lazy";img.decoding="async";img.alt="DigitalRacer catalogue reference photo; finish may differ";img.addEventListener("error",function(){container.replaceChildren();container.insertAdjacentHTML("afterbegin",carSVG)});container.append(img)}else{container.insertAdjacentHTML("afterbegin",carSVG)}return container}
function displayLabel(car){return car.brand+" "+car.model}
function renderVehicles(){
var filtered=all.filter(function(c){return(state.brand==="All"||state.brand===c.brand)&&((c.brand+" "+c.model+" "+c.finish).toLowerCase().includes(state.search))});
var area=$("vehicles");area.replaceChildren();var slice=filtered.slice(0,state.limit);
slice.forEach(function(car){var btn=document.createElement("button");btn.type="button";btn.className="vehicle";btn.setAttribute("aria-pressed",String(state.selected&&state.selected.id===car.id));btn.setAttribute("aria-label","Select "+displayLabel(car)+" "+car.finish);var vis=visual(car,"vehvisual");
var badge=document.createElement("span");badge.className="vehiclebadge";badge.textContent=car.brand.toUpperCase();vis.append(badge);
var tick=document.createElement("span");tick.className="check";tick.textContent="✓";vis.append(tick);btn.append(vis);
var info=document.createElement("div");info.className="vehbody";var h=document.createElement("h3");h.textContent=car.model;info.append(h);var p=document.createElement("p");p.className="finish";p.textContent=car.finish;info.append(p);var t=document.createElement("span");t.className="type";t.textContent=car.type;info.append(t);var cat=document.createElement("span");cat.className="category";cat.textContent=car.origin==="official"?"COLLAB ARCHIVE":car.origin==="store"?"STORE EXAMPLE":"CONCEPT";info.append(cat);btn.append(info);
btn.addEventListener("click",function(){select(car)});area.append(btn)});
text("resultCount",filtered.length+" vehicle finishes");$("empty").hidden=filtered.length!==0;$("more").hidden=state.limit>=filtered.length;
}
function select(car){state.selected=car;text("selected",displayLabel(car)+" — "+car.finish);$("next1").disabled=false;renderVehicles();document.querySelectorAll(".galleryitem").forEach(function(el){el.setAttribute("aria-pressed","false")})}
function step(n){
Array.prototype.forEach.call(document.querySelectorAll(".stage"),function(el){el.hidden=el.id!=="stage-"+n});
for(var i=1;i<=3;i++){var s=$("step-"+i);s.classList.toggle("active",i===Math.min(3,n));s.classList.toggle("done",i<Math.min(3,n));s.setAttribute("aria-current",i===Math.min(3,n)?"step":"false")}
window.scrollTo({top:0,behavior:"smooth"});
}
function showPreview(id){var root=$(id);root.replaceChildren();if(!state.selected)return;var vis=visual(state.selected,"minicar");root.append(vis);var body=document.createElement("div"),h=document.createElement("h3"),p=document.createElement("p");h.textContent=displayLabel(state.selected);p.textContent=state.selected.finish+" · "+state.qty+" car card(s) · presentation demo";body.append(h,p);root.append(body)}
function qty(n){state.qty=Math.max(1,Math.min(10,n));text("qtyValue",state.qty);showPreview("detailPreview")}
function valid(){var uid=$("uid").value.trim(),name=$("nickname").value.trim(),server=$("server").value,region=$("region").value;if(!/^[0-9]{6,20}$/.test(uid))return"Enter a numeric Player UID (6–20 digits) for the demonstration.";if(!name)return"Enter a character nickname.";if(!server||!region)return"Choose both server and country/region.";state.recipient={uid:uid,name:name,server:server,region:region};return""}
function review(){
var err=valid();text("formError",err);if(err)return;
showPreview("reviewPreview");text("r-uid",state.recipient.uid);text("r-nick",state.recipient.name);text("r-server",state.recipient.server);text("r-region",state.recipient.region);text("r-qty",state.qty+" card(s)");
text("r-item",displayLabel(state.selected)+" — "+state.selected.finish);
step(3);
}
function setProgress(n){
$("ring").style.setProperty("--progress",(n/4*100)+"%");text("percent",Math.round(n/4*100)+"%");
for(var i=1;i<=4;i++){var el=$("task-"+i);el.classList.toggle("done",i<=n);el.querySelector("i").textContent=i<=n?"✓":i}
}
function sendDemo(){
if(state.timer){clearInterval(state.timer);state.timer=null}step(4);
$("demoResult").hidden=true;$("demoInProgress").hidden=false;
setProgress(0);var n=0;
state.timer=setInterval(function(){n++;setProgress(n);
if(n===1)text("sendingTitle","Preparing gift request…");
if(n===2)text("sendingTitle","Checking recipient format…");
if(n===3)text("sendingTitle","Simulating card dispatch…");
if(n===4){clearInterval(state.timer);state.timer=null;showReceipt()}
},1100);
}
function showReceipt(){
$("demoInProgress").hidden=true;$("demoResult").hidden=false;
var ref="DR-DEMO-"+String(Date.now()).slice(-8);
text("receiptRef",ref);text("receiptItem",displayLabel(state.selected)+" — "+state.selected.finish);
text("receiptQty",state.qty+" card(s)");text("receiptPlayer",state.recipient.name+" · "+state.recipient.uid);
text("receiptServer",state.recipient.server+" / "+state.recipient.region);
text("receiptDate",new Date().toLocaleString());
}
function reset(){if(state.timer){clearInterval(state.timer);state.timer=null}state.selected=null;state.qty=1;state.recipient=null;$("recipientForm").reset();text("qtyValue",1);text("formError","");text("selected","No vehicle selected");$("next1").disabled=true;renderVehicles();step(1)}
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
$("send").addEventListener("click",sendDemo);
$("restart").addEventListener("click",reset);
renderFilters();renderVehicles();loadGallery();
})();