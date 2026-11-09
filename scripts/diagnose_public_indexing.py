#!/usr/bin/env python3
"""Read-only public HTTP diagnostics for search crawler accessibility.

This is NOT Google Search Console URL Inspection and does not impersonate
verified Googlebot IPs. Only Google Search Console can establish Google's
actual crawl/indexing verdict.
"""
from __future__ import annotations

import json
import os
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlencode
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = "https://www.digitalracer.store"
APEX = "https://digitalracer.store"
MANIFEST = json.loads((ROOT / "p/index.json").read_text(encoding="utf-8"))
PRODUCT = MANIFEST[0]["url"]

PATHS = ["/", "/robots.txt", "/sitemap.xml", "/blog/", PRODUCT, "/this-page-does-not-exist-indexing-check"]
USER_AGENTS = {
    "python": "DigitalRacerIndexingDiagnostic/1.0",
    "browser": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/123 Safari/537.36",
}

def audit(url: str, label: str, ua: str) -> tuple[int | None, str]:
    request = Request(url, headers={"User-Agent": ua, "Accept": "text/html,application/xml,text/plain,*/*"})
    try:
        with urlopen(request, timeout=12) as response:
            status = response.status
            headers = response.headers
            final_url = response.geturl()
            body = response.read(8192).decode("utf-8", "replace")
    except HTTPError as exc:
        status = exc.code
        headers = exc.headers
        final_url = exc.geturl()
        body = exc.read(8192).decode("utf-8", "replace")
    except (URLError, TimeoutError, OSError, socket.timeout) as exc:
        err = exc.reason if isinstance(exc, URLError) else exc
        print(f"{label} {url} -> CONNECTION_ERROR {type(err).__name__}: {str(err)[:160]}", flush=True)
        return None, "connection"

    if urlsplit(final_url).netloc not in {"www.digitalracer.store", "digitalracer.store"}:
        print(f"WARNING: unexpected redirect destination {final_url}", flush=True)
    selected = {k: headers.get(k, "") for k in
                ("Server", "CF-RAY", "Content-Type", "X-Robots-Tag", "Location")}
    indicators = [term for term in
                  ("attention required", "checking your browser", "cloudflare", "access denied", "captcha")
                  if term in body.lower()]
    print(f"{label}: {url} -> {status} final={final_url} headers={selected} body_markers={indicators}",
          flush=True)
    if status in (401, 403, 429, 503):
        print(f"::warning title=Potential crawler access issue::{url} responded with HTTP {status} from {label}", flush=True)
    return status, headers.get("Server", "")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def audit_legacy_redirects() -> None:
    """Make sure legacy product URLs 301, rather than serve noindex stub / 404."""
    opener = build_opener(NoRedirect)
    rules = []
    for raw in (ROOT / "_redirects").read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.startswith("#"):
            continue
        fields = raw.split()
        if len(fields) == 3 and fields[2] == "301":
            rules.append((fields[0], fields[1]))
    failures = []
    good = 0
    for source, target in rules:
        req = Request(HOST + source, headers={"User-Agent": USER_AGENTS["browser"]})
        try:
            with opener.open(req, timeout=8) as response:
                code, location = response.status, response.headers.get("Location", "")
        except HTTPError as exc:
            code, location = exc.code, exc.headers.get("Location", "")
        except (URLError, TimeoutError, OSError) as exc:
            code, location = None, type(exc).__name__
        parsed = urlsplit(location)
        destination = parsed.path if parsed.scheme else location
        if code == 301 and destination == target:
            good += 1
        else:
            failures.append((source, code, location, target))
    print(f"Legacy product redirects: {good}/{len(rules)} exactly match 301 targets.", flush=True)
    for src, code, location, target in failures[:30]:
        print(f"REDIRECT_MISMATCH {src}: status={code} Location={location}, expected=301 {target}", flush=True)
    if failures:
        print(f"::warning title=Legacy redirect failures::{len(failures)} legacy URL rules are not returning expected 301 responses", flush=True)



def audit_legacy_query_redirects() -> None:
    """Verify that the deployed Cloudflare Worker 301s old GSC product URLs."""
    opener = build_opener(NoRedirect)
    cases = [
        ("/product", "PUBG Mobile 660 UC Top-Up – Fast & Secure Global Delivery",
         "/p/pubg-mobile-660-uc-top-up-fast-secure-global-delivery/"),
        ("/product.html", "( Karambit ) And ( Nine-Tails ) 2 In One Deal 🔥pubg mobile card collection",
         "/p/pubg-mobile-karambit-nine-tails-card-bundle-2-in-1-deal-instant/"),
        ("/product", "X ULTIMATES 👑 ANUKHARA X-SUIT (⭐⭐⭐) ❄️ M416 ROARING IMMOLATION MAXX + UMP ANIVERSARRY COMBO (2x LOOT CRATE) 🏎️ LOTUS EMIRA SPORTS",
         "/p/pubg-mobile-account-anukhara-x-suit-3-m416-roaring-immolation-max/"),
    ]
    passed = 0
    for path, title, target in cases:
        endpoint = HOST + path + "?" + urlencode({"item": title})
        req = Request(endpoint, headers={"User-Agent": USER_AGENTS["browser"]})
        try:
            with opener.open(req, timeout=12) as response:
                status, location = response.status, response.headers.get("Location", "")
        except HTTPError as exc:
            status, location = exc.code, exc.headers.get("Location", "")
        except (URLError, TimeoutError, OSError) as exc:
            status, location = None, type(exc).__name__
        redirect_path = urlsplit(location).path
        correct = status == 301 and location == HOST + target
        passed += int(correct)
        print(f"QUERY_REDIRECT {path}: code={status}, dest={redirect_path}, expected={target}, verified={correct}", flush=True)
        if not correct:
            print(f"::warning title=Legacy query canonicalization not live::{path} is not returning the expected 301 for this product", flush=True)
    print(f"Legacy query product redirects: {passed}/{len(cases)} live 301 probes passed.", flush=True)


def main() -> None:
    results = []
    for path in PATHS:
        # Two clients on principal endpoints; one client for remaining routes.
        agents = USER_AGENTS.items() if path in ("/", "/robots.txt") else [("browser", USER_AGENTS["browser"])]
        for label, ua in agents:
            results.append((path, label, *audit(HOST + path, label, ua)))
    results.append(("apex", "browser", *audit(APEX + "/", "browser", USER_AGENTS["browser"])))
    blocked = [(path, label, status) for path, label, status, _ in results
               if status in (401, 403, 429, 503) and path != "/this-page-does-not-exist-indexing-check"]
    if blocked:
        print(f"Potential HTTP accessibility issue for {len(blocked)} of {len(results)} probe requests: {blocked}", flush=True)
    else:
        print("No explicit HTTP 401/403/429/503 responses observed in this environment.", flush=True)
    audit_legacy_redirects()
    audit_legacy_query_redirects()
    print("Note: this public runner is NOT Google's URL Inspection crawler; compare with Search Console.", flush=True)

if __name__ == "__main__":
    main()
