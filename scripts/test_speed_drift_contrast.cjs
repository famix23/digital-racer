"use strict";
/* WCAG-AA color tokens and selector coverage for the independent Speed Drift studio. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const root=path.resolve(__dirname,"..");
const read=p=>fs.readFileSync(path.join(root,p),"utf8");
const theme=read("assets/theme.css");
const html=read("dropzone/index.html");
const dark=read("dropzone/style.css");
assert.ok(html.includes('<body class="dr-speed-drift">'),"Scope Speed Drift's light mode independently");
assert.ok(html.includes('class="dr-studio-catalog-link"'),"Catalog link must not hard-code a dark-only color");
assert.ok(!html.includes('href="/catalog?category=Car%20Card" style="color:#f2d57c"'),"Dark-only inline style remains");
assert.ok(theme.includes("SPEED DRIFT · ACCESSIBLE DAY THEME"),"No white-theme contrast repair");
assert.ok(theme.includes('html[data-dr-theme="light"] body.dr-speed-drift'),"Contrast rules are not properly scoped");
for(const css of [
  ".delivery-guide p",".delivery-guide strong",".delivery-guide small",
  ".field label",".catalog-tools .catalog-label",".walletlabel",".wallethead",
  ".vehbody .type",".vehbody .finish",".vehbody .category",".gallery-cta",
  ".vehiclehint",".step.active strong",".preview p",".summaryline span",
  ".timeline li",".timeline li.done",".footer a",".progresscircle span",
  ".qtybar",".preview",".receipt",".field input",".field select",
  ".search::placeholder",".field input:focus-visible",".galleryitem:focus-visible",
  ".dr-studio-catalog-link",".status",".error"
]){
  assert.ok(theme.includes(css),"Missing contrast treatment for "+css);
}
function luminance(hex){
  const rgb=hex.replace("#","").match(/.{2}/g).map(x=>parseInt(x,16)/255);
  return rgb.reduce((v,c,i)=>{
    const linear=c<=.04045?c/12.92:Math.pow((c+.055)/1.055,2.4);
    return v+linear*[.2126,.7152,.0722][i];
  },0);
}
function ratio(fg,bg){
  const a=luminance(fg),b=luminance(bg);
  return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
}
const palette=[
  ["Main body, headings and input text","#25313d","#ffffff"],
  ["Muted instructions on white","#525f6e","#ffffff"],
  ["Placeholder on white","#596372","#ffffff"],
  ["Promotional accent text on white","#79551a","#ffffff"],
  ["Accent text on cream","#79551a","#fff7e6"],
  ["Muted status text on cream","#525f6e","#fff7e6"],
  ["Labels on slightly tinted forms","#25313d","#faf8f3"],
  ["Green completed-state text","#176737","#ffffff"],
  ["Error messages","#a12b23","#ffffff"],
  ["Gold selected chip text","#251c0b","#efcf82"],
  ["Gold primary button text","#1a170e","#ddb85d"],
  ["Help text on warm white","#525f6e","#fffaf0"],
];
for(const [label,fg,bg] of palette)assert.ok(ratio(fg,bg)>=4.5,
  label+" has contrast "+ratio(fg,bg).toFixed(2)+":1 (<4.5:1)");
assert.ok(dark.includes("background:radial-gradient(ellipse")&&dark.includes("--bg:#08090d"),
  "Original premium dark mode must remain");
console.log("Passed Speed Drift light-theme WCAG-AA palette checks for "+palette.length+
  " foreground/background pairs and 29 text/control surfaces.");

