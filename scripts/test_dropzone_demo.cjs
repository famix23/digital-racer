"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const read = p => fs.readFileSync(path.join(root, p), "utf8");
const html = read("dropzone/index.html");
const styles = read("dropzone/style.css");
const script = read("dropzone/app.js");
const catalog = read("dropzone/catalog.js");
const paymentConfig = read("dropzone/payment-config.js");
const homepage = read("index.html");
const headers = read("_headers");

for(const [file,source] of [["app.js",script],["catalog.js",catalog],["payment-config.js",paymentConfig]]){
  new vm.Script(source, {filename:file});
}
const sandbox = {window:{}};
vm.runInNewContext(catalog,sandbox);
vm.runInNewContext(paymentConfig,sandbox);
const cars = sandbox.window.DROPZONE_CARS;
const images = sandbox.window.SPEED_DRIFT_BRAND_IMAGES;
const payment = sandbox.window.SPEED_DRIFT_PAYMENT;
assert.ok(Array.isArray(cars) && cars.length >= 45);
for(const brand of ["Bentley","Ferrari","Lamborghini","Bugatti","Pagani","Dodge","McLaren","Porsche","Koenigsegg","Aston Martin"]) {
  assert.ok(cars.some(c => c.brand === brand),"Missing brand "+brand);
  assert.ok(images[brand]?.startsWith("/images/uploads/"),"Missing default imagery for "+brand);
}
assert.ok(cars.every(c => c.image?.startsWith("/images/uploads/")),"Every vehicle needs an image path");
assert.equal(new Set(cars.map(c => [c.brand,c.model,c.finish].join(":"))).size,cars.length,"Duplicate variant");
assert.equal(payment.network,"TRON (TRC20)");
assert.equal(payment.unitPriceUSD,120,"Car card USD unit price");
assert.equal(payment.unitPriceUSDT,120,"USDT unit amount");
assert.ok(html.includes("id=\"detailTotal\"") && html.includes("id=\"reviewTotal\"") && html.includes("id=\"paymentTotal\""),"Price totals must render at every stage");
assert.ok(!/Speed Drift\s*<span[^>]*>\s*Demo\s*<\/span>/i.test(homepage),"Homepage demo badge must be removed");
assert.match(payment.walletAddress,/^T[1-9A-HJ-NP-Za-km-z]{33}$/);
assert.ok(html.includes('src="/dropzone/payment-config.js"'),"Payment settings must load before app.js");
const ids = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]));
for(const match of script.matchAll(/\$\("([A-Za-z0-9-]+)"\)/g)) {
  assert.ok(ids.has(match[1]),"JS references missing HTML ID "+match[1]);
}
for(const n of [1,2,3,4,5]) assert.ok(ids.has("stage-"+n),"Missing stage "+n);
for(const id of ["uid","nickname","server","region","qtyValue","walletAddress","txHash","paymentPreview","statusPreview","copyWallet","requestQuote","requestVerification","backPayment","backStatus","sendDetailsLink"]) {
  assert.ok(ids.has(id),"Missing field or control "+id);
}
assert.ok(html.includes('name="robots" content="noindex'));
assert.ok(headers.split("/dropzone/*")[1]?.includes("noindex"),"Site must exclude utility page from SEO");
assert.ok(homepage.includes('href="/dropzone/"'),"Homepage must link to Speed Drift");
assert.ok(html.includes("Pending merchant verification"),"Payment cannot be confirmed without a verification service");
assert.ok(html.includes("Not confirmed"),"Gift delivery cannot be confirmed automatically");
assert.ok(!/type=["']password["']/.test(html),"Do not collect passwords");
assert.ok(styles.includes("@media(max-width:520px)"),"Missing mobile layout");
assert.ok(script.includes('fetch("/inventory.json"'),"Read existing product photo gallery");
console.log("Speed Drift static checks passed:",cars.length,"vehicle variants; payment address configured; five stages.");
