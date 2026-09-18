#!/usr/bin/env python3
"""Check every link and image in the built site (run `python3 build.py` first).

    python3 check_links.py            # internal + external links
    python3 check_links.py --local    # internal links only (no network)
"""
import argparse
import re
import ssl
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin

OUT = Path(__file__).resolve().parent / "_site"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
# Sites that refuse scripted requests; a 403/429/999 from them does not mean the link is broken
BOT_WALLS = ("linkedin.com", "ieeexplore.ieee.org", "scholar.google.com", "researchgate.net")


def collect():
    links = {}
    for page in OUT.rglob("*.html"):
        url_path = "/" + str(page.relative_to(OUT)).replace("index.html", "")
        for attr, raw in re.findall(r'\b(href|src)="([^"]+)"', page.read_text(encoding="utf-8")):
            if raw.startswith(("mailto:", "javascript:", "data:")) or raw.startswith("#"):
                continue
            target = urldefrag(urljoin(url_path, raw.replace("&amp;", "&")))[0]
            links.setdefault(target, set()).add(url_path)
    return links


def check_local(url):
    path = OUT / unquote(url.lstrip("/"))
    return path.is_file() or (path / "index.html").is_file()


def check_remote(url, verify=True):
    ctx = ssl.create_default_context() if verify else ssl._create_unverified_context()
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
                return r.status, r.url
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 404, 405, 429, 500, 501, 503):
                continue  # some servers reject HEAD; retry with GET
            return e.code, url
        except urllib.error.URLError as e:
            if verify and isinstance(e.reason, ssl.SSLCertVerificationError):
                status, final = check_remote(url, verify=False)  # server sends an incomplete cert chain;
                return f"CERT-{status}", final                  # browsers cope, Python does not
            if method == "GET":
                return type(e).__name__, url
        except Exception as e:
            if method == "GET":
                return type(e).__name__, url
    return "?", url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true")
    args = ap.parse_args()
    links = collect()
    local = sorted(u for u in links if u.startswith("/"))
    remote = sorted(u for u in links if u.startswith("http") and "fonts.g" not in u)
    bad = 0

    print(f"Internal: {len(local)} links")
    for u in local:
        if not check_local(u):
            bad += 1
            print(f"  BROKEN  {u}   (on {', '.join(sorted(links[u]))})")

    if not args.local:
        print(f"External: {len(remote)} links")
        with ThreadPoolExecutor(12) as pool:
            for u, (status, final) in zip(remote, pool.map(check_remote, remote)):
                if isinstance(status, int) and 200 <= status < 300:
                    continue
                walled = any(d in u for d in BOT_WALLS) and status in (403, 429, 999, 418)
                cert_ok = str(status) in ("CERT-200", "CERT-202")
                tag = "BLOCKED" if walled else "OK*    " if cert_ok else "BROKEN "
                bad += not (walled or cert_ok)
                print(f"  {tag} {status}  {u}   (on {', '.join(sorted(links[u]))})")
    print("BLOCKED = site refuses scripts (check by hand); OK* = works in browsers, incomplete TLS chain")
    print("All links OK." if not bad else f"{bad} broken link(s).")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
