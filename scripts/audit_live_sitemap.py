#!/usr/bin/env python3
"""Read-only, external GET audit of every canonical URL listed in the sitemap.

This checks deployed HTTP responses. It cannot inspect Google's private
Page Indexing status or impersonate verified Googlebot requests.
"""
from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import html
import re
import socket
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOST = "https://www.digitalracer.store"
TIMEOUT = 12
UA = "DigitalRacer-IndexabilityAudit/1.0 (public HTTP health check)"
CANONICAL = re.compile(r'<link\s+rel="canonical"\s+href="([^"]+)"', re.I)
NOINDEX = re.compile(r'<meta\s+name="(?:robots|googlebot)"\s+content="[^"]*\bnoindex\b', re.I)

def test(url: str) -> tuple[str, int | None, str, str | None]:
    # Retry transient connection failures, and slow down on server load signals.
    for attempt in range(3):
        req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
        try:
            with urlopen(req, timeout=TIMEOUT) as response:
                status = response.status
                final = response.geturl()
                header_noindex = response.headers.get("X-Robots-Tag", "")
                page = response.read(24000).decode("utf-8", "replace")
        except HTTPError as exc:
            status, final, header_noindex = exc.code, exc.geturl(), exc.headers.get("X-Robots-Tag", "")
            page = exc.read(3000).decode("utf-8", "replace")
        except (URLError, TimeoutError, OSError, socket.timeout) as exc:
            if attempt < 2:
                time.sleep((attempt + 1) * 0.5)
                continue
            return url, None, "", f"Network failure: {type(exc).__name__}: {str(exc)[:120]}"
        if status in (429, 500, 502, 503, 504) and attempt < 2:
            time.sleep((attempt + 1) * 1.0)
            continue
        if status != 200:
            return url, status, final, f"Unexpected HTTP status {status}"
        if final.rstrip("/") != url.rstrip("/"):
            return url, status, final, "Unexpected redirect from canonical sitemap URL"
        if "noindex" in header_noindex.lower():
            return url, status, final, "X-Robots-Tag blocks indexing"
        if NOINDEX.search(page):
            return url, status, final, "HTML robots noindex"
        match = CANONICAL.search(page)
        if not match:
            return url, status, final, "Canonical element absent from first 24KB of HTML"
        declared = html.unescape(match.group(1))
        if declared != url:
            return url, status, final, f"Canonical mismatch: {declared[:150]}"
        return url, status, final, None
    raise AssertionError("Unreachable retry loop")

def main() -> None:
    sitemap = ET.parse(ROOT / "sitemap.xml")
    urls = [item.find("{*}loc").text for item in sitemap.findall("{*}url")]
    if not urls or len(urls) != len(set(urls)):
        raise SystemExit("Sitemap is empty or contains duplicate canonical URLs")
    if any(urlsplit(u).scheme + "://" + urlsplit(u).netloc != HOST for u in urls):
        raise SystemExit("Sitemap contains external or wrong-host URLs")
    failures = []
    status_counts = Counter()
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(test, url) for url in urls]
        for future in as_completed(futures):
            url, status, final, issue = future.result()
            status_counts[str(status) if status is not None else "network"] += 1
            if issue:
                failures.append((url, issue, final))
    print(f"Live sitemap audit: {len(urls)} canonical URLs tested.", flush=True)
    print("HTTP status distribution: " +
          ", ".join(f"{status}={count}" for status, count in sorted(status_counts.items())), flush=True)
    print(f"Correct live 200 + self-canonical + indexable: {len(urls)-len(failures)}/{len(urls)}", flush=True)
    for url, issue, final in sorted(failures)[:60]:
        print(f"INDEXING_FAILURE {url} | {issue} | reached={final}", flush=True)
    if failures:
        raise SystemExit(f"Failed: {len(failures)} sitemap URLs have actionable HTTP/indexing defects.")
    print("Passed: all sitemap pages are publicly fetchable with their own canonical and no noindex.", flush=True)

if __name__ == "__main__":
    main()
