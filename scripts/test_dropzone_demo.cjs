"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname,"..");
const read = p => fs.readFileSync(path.join(root,p),"utf8");
const html = read("dropzone/index.html");
const styles = read("dropzone/style.css");
const script = read("dropzone/app.js");
const catalog = read("dropzone/catalog.js");
const homepage = read("index.html");
const headers = read("_headers");
new vm.Script(script,{filename:"dropzone/app.js"});
new vm.Script(catalog,{filename:"dropzone/catalog.js"});
const sandbox = {window:{}};
vm.runInNewContext(catalog,sandbox);
const cars = sandbox.window.DROPZONE_CARS;
assert.ok(Array.isArray(cars)&&cars.length>=45,"Vehicle collection should have at least 45 variants");
for (const brand of ["Bentley","Ferrari","Lamborghini","Bugatti","Pagani","Dodge"]) {
  assert.ok(cars.some(c=>c.brand===brand),"Missing brand: "+brand);
}
assert.equal(new Set(cars.map(c=>[c.brand,c.model,c.finish].join(":"))).size,cars.length,"Duplicate variant");
const htmlIds = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]));
for(const match of script.matchAll(/\$\("([A-Za-z0-9-]+)"\)/g)) {
  assert.ok(htmlIds.has(match[1]),"JS references missing HTML ID "+match[1]);
}
for(const stage of [1,2,3,4])assert.ok(htmlIds.has("stage-"+stage),"Missing step "+stage);
for(const id of ["uid","nickname","server","region","qtyValue","demoResult","receiptRef","storeGallery"])assert.ok(htmlIds.has(id),"Missing form/result ID "+id);
assert.ok(/noindex/.test(html),"Demo landing page must be noindex");
assert.ok(/X-Robots-Tag: noindex/.test(headers.split("/dropzone/*")[1]||""),"Missing demo response noindex");
assert.ok(homepage.includes('href="/dropzone/"'),"Homepage must link to DropZone");
assert.ok(/No in-game item was delivered/i.test(html),"Demo receipt must disclaim delivery");
assert.ok(/No gift is transferred/i.test(html),"Review must explain simulation");
assert.ok(!/type=["']password["']/.test(html),"Do not collect game credentials");
assert.ok(!/fetch\([^)]*,\s*\{[^}]*method:\s*["']POST/i.test(script),"Demo must not submit player details");
assert.ok(styles.includes("@media(max-width:520px)"),"Missing mobile layout");
assert.ok(/fetch\("\/inventory.json"/.test(script),"Gallery should use live DigitalRacer catalog imagery");
console.log("Speed Drift static checks passed:",cars.length,"vehicle examples,",htmlIds.size,"HTML IDs.");
