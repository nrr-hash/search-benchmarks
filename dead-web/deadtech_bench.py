#!/usr/bin/env python3
"""
deadtech_bench.py - does the declared, free, machine-readable web still work?

For every domain in a fixed seed list, this fetches, over plain HTTPS:
  1. /robots.txt                      -> present? does it declare Sitemap:?
  2. the declared sitemap, else /sitemap.xml
  3. the homepage HTML                -> is an RSS/Atom feed autodiscovered?
  4. that feed                        -> does it parse, how many items, how fresh?

It records wall-clock latency and HTTP status for every request, and it counts
failures as failures. Nothing is retried, nothing is imputed, nothing is
dropped for looking wrong.

Usage:  python3 deadtech_bench.py seeds.txt out.json [--timeout 15]

Standard library only. One thread, sequential, politely paced.
"""
import json, re, ssl, sys, time, gzip, io
import urllib.request, urllib.error
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET
from datetime import datetime, timezone

UA = "deadtech-bench/1.0 (reproducible measurement; contact in the write-up)"
TIMEOUT = 15

def get(url, timeout=TIMEOUT, limit=3_000_000):
    """Return (status, bytes, seconds, error). Never raises."""
    t0 = time.monotonic()
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "*/*", "Accept-Encoding": "gzip",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(limit)
            if r.headers.get("Content-Encoding") == "gzip":
                try: body = gzip.decompress(body)
                except Exception: pass
            return r.status, body, round(time.monotonic() - t0, 3), None
    except urllib.error.HTTPError as e:
        return e.code, b"", round(time.monotonic() - t0, 3), f"HTTPError {e.code}"
    except Exception as e:
        return None, b"", round(time.monotonic() - t0, 3), f"{type(e).__name__}: {str(e)[:120]}"

FEED_LINK = re.compile(
    r"""<link[^>]+(?:type=["']application/(?:rss|atom)\+xml["'][^>]*href=["']([^"']+)["']"""
    r"""|href=["']([^"']+)["'][^>]*type=["']application/(?:rss|atom)\+xml["'])""", re.I)

CONVENTIONAL_FEEDS = ["/feed", "/rss", "/rss.xml", "/atom.xml", "/feed.xml", "/index.xml"]

def parse_sitemap(body):
    """Return (kind, url_count, lastmod_values) or (None, 0, [])."""
    try:
        root = ET.fromstring(body)
    except Exception:
        return None, 0, []
    tag = root.tag.split("}")[-1]
    ns = {"s": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
    def findall(path):
        return root.findall(path, ns) if ns else root.findall(path.replace("s:", ""))
    if tag == "sitemapindex":
        kids = findall("s:sitemap")
        lm = [e.text.strip() for s in kids for e in s.findall("s:lastmod", ns) if e.text] if ns \
             else [e.text.strip() for s in kids for e in s.findall("lastmod") if e.text]
        return "sitemapindex", len(kids), lm
    if tag == "urlset":
        kids = findall("s:url")
        lm = [e.text.strip() for u in kids for e in u.findall("s:lastmod", ns) if e.text] if ns \
             else [e.text.strip() for u in kids for e in u.findall("lastmod") if e.text]
        return "urlset", len(kids), lm
    return tag, 0, []

def parse_feed(body):
    try:
        root = ET.fromstring(body)
    except Exception:
        return None, 0, []
    tag = root.tag.split("}")[-1]
    if tag == "rss":
        items = root.findall(".//item")
        dates = [e.text for i in items for e in i.findall("pubDate") if e is not None and e.text]
        return "rss", len(items), dates[:5]
    if tag == "feed":
        entries = [e for e in root if e.tag.split("}")[-1] == "entry"]
        dates = [c.text for e in entries for c in e
                 if c.tag.split("}")[-1] in ("updated", "published") and c.text]
        return "atom", len(entries), dates[:5]
    return tag, 0, []

def age_days(values):
    """Youngest lastmod/pubDate in days, or None if nothing parses."""
    best = None
    now = datetime.now(timezone.utc)
    for v in values[:50]:
        d = None
        v = v.strip()
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%d",
                    "%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
            try:
                d = datetime.strptime(v.replace("Z", "+0000"), fmt)
                break
            except ValueError:
                continue
        if d is None:
            continue
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        days = (now - d).total_seconds() / 86400
        if best is None or days < best:
            best = days
    return round(best, 2) if best is not None else None

def probe(domain):
    base = f"https://{domain}/"
    rec = {"domain": domain}

    st, body, secs, err = get(base + "robots.txt")
    rec["robots"] = {"status": st, "seconds": secs, "error": err, "bytes": len(body)}
    declared = []
    if st == 200 and body:
        text = body.decode("utf-8", "replace")
        declared = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", text)
    rec["robots"]["declares_sitemap"] = bool(declared)
    rec["robots"]["declared_sitemaps"] = declared[:5]

    sm_url = declared[0] if declared else urljoin(base, "/sitemap.xml")
    st, body, secs, err = get(sm_url)
    kind, count, lastmods = parse_sitemap(body) if st == 200 else (None, 0, [])
    rec["sitemap"] = {"url": sm_url, "from_robots": bool(declared), "status": st,
                      "seconds": secs, "error": err, "bytes": len(body),
                      "parsed_kind": kind, "entries": count,
                      "entries_with_lastmod": len(lastmods),
                      "youngest_lastmod_days": age_days(lastmods)}

    st, body, secs, err = get(base)
    rec["homepage"] = {"status": st, "seconds": secs, "error": err, "bytes": len(body)}
    feed_url = None
    if st == 200 and body:
        html = body.decode("utf-8", "replace")
        m = FEED_LINK.search(html)
        if m:
            feed_url = urljoin(base, m.group(1) or m.group(2))
    rec["feed_autodiscovered"] = bool(feed_url)

    if not feed_url:
        for path in CONVENTIONAL_FEEDS:
            st2, body2, secs2, err2 = get(urljoin(base, path), timeout=8)
            if st2 == 200 and parse_feed(body2)[0] in ("rss", "atom"):
                feed_url = urljoin(base, path)
                break

    if feed_url:
        st, body, secs, err = get(feed_url)
        kind, items, dates = parse_feed(body) if st == 200 else (None, 0, [])
        rec["feed"] = {"url": feed_url, "autodiscovered": rec["feed_autodiscovered"],
                       "status": st, "seconds": secs, "error": err,
                       "parsed_kind": kind, "items": items,
                       "youngest_item_days": age_days(dates)}
    else:
        rec["feed"] = {"url": None, "autodiscovered": False, "status": None,
                       "seconds": None, "error": "no feed found",
                       "parsed_kind": None, "items": 0, "youngest_item_days": None}
    return rec

def main():
    seeds_path, out_path = sys.argv[1], sys.argv[2]
    seeds = []
    for line in open(seeds_path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        cat, _, dom = line.partition(":")
        seeds.append((cat, dom))
    started = datetime.now(timezone.utc).isoformat()
    results = []
    for i, (cat, dom) in enumerate(seeds, 1):
        r = probe(dom)
        r["category"] = cat
        results.append(r)
        print(f"[{i}/{len(seeds)}] {dom:34s} robots={r['robots']['status']} "
              f"sitemap={r['sitemap']['status']}/{r['sitemap']['entries']} "
              f"feed={r['feed']['parsed_kind']}", file=sys.stderr, flush=True)
        time.sleep(0.4)
    json.dump({"run_started_utc": started,
               "run_finished_utc": datetime.now(timezone.utc).isoformat(),
               "seed_count": len(seeds), "user_agent": UA, "timeout_s": TIMEOUT,
               "results": results}, open(out_path, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"wrote {out_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
