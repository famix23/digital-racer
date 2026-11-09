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
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
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
    print("Note: this public runner is NOT Google's URL Inspection crawler; compare with Search Console.", flush=True)

if __name__ == "__main__":
    main()
