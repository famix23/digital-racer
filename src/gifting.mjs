import {adminPage} from "./gifting-ui.mjs";

const BASE="https://www.digitalracer.store";
const ID=/^[a-f0-9]{64}$/;
const HEADERS={"Cache-Control":"private, no-store, max-age=0","X-Robots-Tag":"noindex, nofollow, noarchive","Referrer-Policy":"no-referrer","X-Content-Type-Options":"nosniff","X-Frame-Options":"DENY","Content-Security-Policy":"default-src 'none'; img-src 'self' data: blob:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"};
const json=(v,status=200)=>new Response(JSON.stringify(v),{status,headers:{...HEADERS,"Content-Type":"application/json; charset=utf-8"}});
const html=(v,status=200)=>new Response(v,{status,headers:{...HEADERS,"Content-Type":"text/html; charset=utf-8"}});
const fail=(msg,status=400)=>json({error:msg},status);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const token=()=>Array.from(crypto.getRandomValues(new Uint8Array(32)),v=>v.toString(16).padStart(2,"0")).join("");
const text=(v,max)=>typeof v==="string"&&v.trim().length>0&&v.trim().length<=max?v.trim():null;
const states=["Pending","Preparing","Delivered"];
const expiry=30*86400000;
const imageOK=s=>typeof s==="string"&&s.length<=550000&&/^data:image\/jpeg;base64,\/9j\/[A-Za-z0-9+/]+={0,2}$/.test(s);
export function validGift(v){
 if(!v||typeof v!=="object")return null;
 const name=text(v.name,240),variant=typeof v.variant==="string"&&v.variant.length<=120?v.variant.trim():null,uid=text(v.uid,20),nickname=text(v.nickname,64),region=text(v.region,80),country=text(v.country,80);
 if(!name||variant===null||!uid||!/^\d{5,20}$/.test(uid)||!nickname||!region||!country||!Array.isArray(v.images)||v.images.length<1||v.images.length>4||!v.images.every(imageOK))return null;
 return {name,variant,uid,nickname,region,country,images:v.images};
}
async function authorized(request,env){
 const secret=env.GIFT_ADMIN_TOKEN;
 if(typeof secret!=="string"||secret.length<32)return false;
 const provided=request.headers.get("Authorization")||"";
 if(provided.length>1024)return false;
 const digest=async s=>new Uint8Array(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s)));
 const [a,b]=await Promise.all([digest(provided),digest("Bearer "+secret)]);
 let diff=0;for(let i=0;i<a.length;i++)diff|=a[i]^b[i];return diff===0;
}
async function boundedJSON(request){
 const reader=request.body?.getReader();if(!reader)throw Error("Missing body");
 let total=0;const decoder=new TextDecoder();let raw="";
 try{while(true){const {done,value}=await reader.read();if(done)break;total+=value.byteLength;if(total>2300000){await reader.cancel();throw Error("Too large")}raw+=decoder.decode(value,{stream:true})}raw+=decoder.decode();return JSON.parse(raw)}finally{reader.releaseLock()}
}
const pageCSS="*{box-sizing:border-box}body{margin:0;background:#09090d;color:#f5f3ef;font:16px/1.55 system-ui,sans-serif}main{max-width:880px;margin:auto;padding:22px}header{display:flex;align-items:center;justify-content:space-between;gap:12px;border-bottom:1px solid #333;padding:15px 0;flex-wrap:wrap}.brand,.gold{color:#ebc970}.brand{font-weight:900;letter-spacing:.15em}.eyebrow{font-size:.75rem;text-transform:uppercase;letter-spacing:.13em;color:#ebc970}h1{line-height:1.1;font-size:clamp(1.7rem,5vw,2.8rem);overflow-wrap:anywhere}h2{font-size:1.15rem}.card{border:1px solid #36343d;border-radius:18px;background:#15151c;padding:20px;margin:20px 0}.hero{display:block;width:100%;max-height:600px;object-fit:contain;background:#09090d;border-radius:12px}.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-top:10px}.gallery img{width:100%;border-radius:8px;object-fit:contain}.muted{color:#bdbbc5}.line{display:flex;justify-content:space-between;gap:18px;border-bottom:1px solid #333;padding:10px 0;overflow-wrap:anywhere}.line strong{text-align:right;max-width:65%}.status{display:inline-block;border:1px solid #827040;border-radius:999px;padding:5px 12px;color:#ebc970}.foot{font-size:.82rem;color:#bdbbc5;margin-top:24px}@media(max-width:500px){main{padding:14px}.card{padding:14px}}";
export function customerPage(record,images){
 const ref=record.id.slice(0,12).toUpperCase();
 const rows=[["Player ID number",record.uid],["Player ID name",record.nickname],["Region",record.region],["Country",record.country],["Gift reference",ref]];
 return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow,noarchive"><title>DigitalRacer | Gift details</title><style>'+pageCSS+'</style></head><body><main><header><span class="brand">DIGITAL.RACER</span><span class="eyebrow">Private gifting studio</span></header><section class="card"><div class="eyebrow">Your selected gift</div><h1>'+esc(record.name)+'</h1><p class="gold">'+esc(record.variant)+'</p><img class="hero" src="'+esc(images[0])+'" alt="'+esc(record.name)+'">'+(images.length>1?'<div class="gallery">'+images.slice(1).map((s,i)=>'<img src="'+esc(s)+'" alt="Selected gift image '+(i+2)+'">').join("")+'</div>':"")+'</section><section class="card"><h2>Recipient information</h2>'+rows.map(([a,b])=>'<div class="line"><span class="muted">'+esc(a)+'</span><strong>'+esc(b)+'</strong></div>').join("")+'<p><span class="status">'+esc(record.status)+'</span></p><p class="muted">'+(record.status==="Delivered"?"Marked delivered by DigitalRacer after manual verification.":"In-game delivery is handled manually by DigitalRacer. This page is not a confirmation of delivery.")+'</p></section><p class="foot">Private link. Do not forward without the recipient’s permission. DigitalRacer is an independent service, not affiliated with PUBG MOBILE.</p></main></body></html>';
}
const notFound=()=>html('<!doctype html><meta name="viewport" content="width=device-width"><title>Gift unavailable</title><p>This gift link is unavailable, expired or revoked.</p>',404);
export class GiftStore{
 constructor(ctx){
  this.ctx=ctx;this.sql=ctx.storage.sql;
  this.sql.exec("CREATE TABLE IF NOT EXISTS gifts (id TEXT PRIMARY KEY, data TEXT NOT NULL, created INTEGER NOT NULL, expires INTEGER NOT NULL)");
  this.sql.exec("CREATE TABLE IF NOT EXISTS gift_images (gift_id TEXT NOT NULL, position INTEGER NOT NULL, image TEXT NOT NULL, PRIMARY KEY(gift_id,position))");
 }
 cleanup(){
  this.ctx.storage.transactionSync(()=>{this.sql.exec("DELETE FROM gift_images WHERE gift_id IN (SELECT id FROM gifts WHERE expires <= ?)",Date.now());this.sql.exec("DELETE FROM gifts WHERE expires <= ?",Date.now())});
 }
 async fetch(request){
  const path=new URL(request.url).pathname,method=request.method;this.cleanup();
  if(path==="/list"&&method==="GET"){const rows=this.sql.exec("SELECT data FROM gifts ORDER BY created DESC LIMIT 200").toArray();return json({gifts:rows.map(r=>JSON.parse(r.data))})}
  if(path==="/create"&&method==="POST"){
   let input;try{input=validGift(await boundedJSON(request))}catch{return fail("Invalid request")}
   if(!input)return fail("Check the four recipient fields, product name and 1–4 JPEG images.");
   const {images,...fields}=input,id=token(),created=Date.now(),record={...fields,id,status:"Pending",created,expires:created+expiry};
   this.ctx.storage.transactionSync(()=>{this.sql.exec("INSERT INTO gifts VALUES (?,?,?,?)",id,JSON.stringify(record),created,record.expires);images.forEach((image,i)=>this.sql.exec("INSERT INTO gift_images VALUES (?,?,?)",id,i,image))});
   return json({gift:record,url:BASE+"/gift/"+id+"/"},201);
  }
  const match=path.match(/^\/(view|status|revoke)\/([a-f0-9]{64})$/);if(!match)return fail("Not found",404);
  const [,action,id]=match,rows=this.sql.exec("SELECT data FROM gifts WHERE id=?",id).toArray();if(!rows.length)return action==="view"?notFound():fail("Gift unavailable",404);
  const record=JSON.parse(rows[0].data);
  if(action==="view"&&(method==="GET"||method==="HEAD")){
   const images=this.sql.exec("SELECT image FROM gift_images WHERE gift_id=? ORDER BY position",id).toArray().map(x=>x.image);
   const result=customerPage(record,images);return method==="HEAD"?new Response(null,{headers:{...HEADERS,"Content-Type":"text/html; charset=utf-8"}}):html(result);
  }
  if(action==="status"&&method==="POST"){
   let value;try{value=(await boundedJSON(request)).status}catch{return fail("Invalid status")}
   if(!states.includes(value))return fail("Invalid status");
   record.status=value;this.sql.exec("UPDATE gifts SET data=? WHERE id=?",JSON.stringify(record),id);return json({gift:record});
  }
  if(action==="revoke"&&method==="POST"){
   this.ctx.storage.transactionSync(()=>{this.sql.exec("DELETE FROM gift_images WHERE gift_id=?",id);this.sql.exec("DELETE FROM gifts WHERE id=?",id)});return json({revoked:true});
  }
  return fail("Method not allowed",405);
 }
}
export async function giftRoute(request,env){
 const path=new URL(request.url).pathname,method=request.method;
 const admin=path==="/admin/gifting"||path.startsWith("/admin/gifting/");
 const pub=path==="/gift"||path.startsWith("/gift/");
 if(!admin&&!pub)return null;
 if(!env.GIFT_STORE||typeof env.GIFT_ADMIN_TOKEN!=="string"||env.GIFT_ADMIN_TOKEN.length<32)return html("<!doctype html><title>Gifting unavailable</title><p>Gifting studio is not configured.</p>",503);
 const stub=env.GIFT_STORE.get(env.GIFT_STORE.idFromName("private-gifts-v1"));
 if(pub){
  const m=path.match(/^\/gift\/([a-f0-9]{64})\/?$/);if(!m||!["GET","HEAD"].includes(method))return notFound();
  return stub.fetch("https://gift.internal/view/"+m[1],{method});
 }
 if((path==="/admin/gifting"||path==="/admin/gifting/")&&method==="GET")return html(adminPage);
 if(!await authorized(request,env))return fail("Administrator authentication required",401);
 const suffix=path.replace(/^\/admin\/gifting\/api/,"");
 if(!path.startsWith("/admin/gifting/api/"))return fail("Not found",404);
 if(suffix==="/list"&&method==="GET")return stub.fetch("https://gift.internal/list");
 if(suffix==="/create"&&method==="POST"){
  let data;try{data=validGift(await boundedJSON(request))}catch{return fail("Invalid request")}
  if(!data)return fail("Check recipient details and images");
  return stub.fetch("https://gift.internal/create",{method:"POST",body:JSON.stringify(data)});
 }
 const m=suffix.match(/^\/(status|revoke)\/([a-f0-9]{64})$/);
 if(m&&method==="POST"){let data={};if(m[1]==="status"){try{data=await boundedJSON(request)}catch{return fail("Invalid status")}}return stub.fetch("https://gift.internal/"+m[1]+"/"+m[2],{method:"POST",body:JSON.stringify(data)})}
 return fail("Not found",404);
}
