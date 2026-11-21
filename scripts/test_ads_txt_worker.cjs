#!/usr/bin/env node
// Verify the Cloudflare Worker returns a plain-text Google ads.txt record.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {pathToFileURL} = require("node:url");

(async function main() {
  const root = path.resolve(__dirname, "..");
  const expected = fs.readFileSync(path.join(root, "ads.txt"), "utf8");
  const configText = fs.readFileSync(path.join(root, "wrangler.jsonc"), "utf8");
  const config = JSON.parse(configText.replace(/^\s*\/\/.*$/gm, ""));
  assert(config.assets.run_worker_first.includes("/ads.txt"), "ads.txt must run Worker first");

  const {default: worker} = await import(pathToFileURL(path.join(root, "src/worker.mjs")).href);
  const env = {ASSETS: {fetch() { throw new Error("ads.txt must not depend on assets"); }}};
  for (const hostname of ["www.digitalracer.store", "digitalracer.store"]) {
    for (const method of ["GET", "HEAD"]) {
      const response = await worker.fetch(new Request(`https://${hostname}/ads.txt`, {method}), env);
      assert.equal(response.status, 200, `${hostname} ${method}`);
      assert.match(response.headers.get("Content-Type") || "", /^text\/plain\b/i);
      assert.equal(await response.text(), method === "HEAD" ? "" : expected);
    }
  }
  console.log("Worker ads.txt passes for both hosts (GET and HEAD), matching root ads.txt.");
})().catch(error => {console.error(error); process.exitCode = 1;});
