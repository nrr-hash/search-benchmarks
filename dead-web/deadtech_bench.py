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
import argparse, hashlib, json, re, sys, time, gzip, io
from html.parser import HTMLParser
from email.utils import parsedate_to_datetime
import urllib.request, urllib.error
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET
from datetime import datetime, timezone

UA = "deadtech-bench/1.1 (reproducible measurement; contact in the write-up)"
TIMEOUT = 15

def get(url, timeout=TIMEOUT, limit=3_000_000):
    """Return (status, bytes, seconds, error). Never raises."""
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "*/*", "Accept-Encoding": "gzip",
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(limit + 1)
            if len(body) > limit:
                raise ValueError("response exceeds download limit")
            if (r.headers.get("Content-Encoding") or "").lower() == "gzip" or body.startswith(b"\x1f\x8b"):
                with gzip.GzipFile(fileobj=io.BytesIO(body)) as stream:
                    body = stream.read(limit + 1)
                if len(body) > limit:
                    raise ValueError("response exceeds decompressed limit")
            return r.status, body, round(time.monotonic() - t0, 3), None
    except urllib.error.HTTPError as e:
        return e.code, b"", round(time.monotonic() - t0, 3), f"HTTPError {e.code}"
    except Exception as e:
        return None, b"", round(time.monotonic() - t0, 3), f"{type(e).__name__}: {str(e)[:120]}"

class FeedLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if (tag == "link" and "alternate" in (a.get("rel") or "").lower().split()
                and (a.get("type") or "").lower().split(";")[0].strip()
                in ("application/rss+xml", "application/atom+xml") and a.get("href")):
            self.links.append(a["href"])

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
        return "rss", len(items), dates
    if tag == "feed":
        entries = [e for e in root if e.tag.split("}")[-1] == "entry"]
        dates = [c.text for e in entries for c in e
                 if c.tag.split("}")[-1] in ("updated", "published") and c.text]
        return "atom", len(entries), dates
    if root.tag == "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF":
        items = root.findall("{http://purl.org/rss/1.0/}item")
        dates = [e.text for i in items for e in i.findall("{http://purl.org/dc/elements/1.1/}date") if e.text]
        return "rss1", len(items), dates
    return tag, 0, []

def age_days(values, now=None):
    """Youngest non-future timestamp across all supplied values; missing is None."""
    now = now or datetime.now(timezone.utc)
    ages = []
    for value in values:
        value = value.strip()
        try:
            d = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                d = parsedate_to_datetime(value)
            except (ValueError, TypeError, OverflowError):
                continue
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        age = (now - d).total_seconds() / 86400
        # Year-one placeholders and future dates are not evidence of freshness.
        if d.year >= 1970 and age >= 0:
            ages.append(age)
    return round(min(ages), 2) if ages else None

def probe(domain, timeout=TIMEOUT):
    base = f"https://{domain}/"
    rec = {"domain": domain, "requests": []}
    def fetch(url):
        result = get(url, timeout=timeout)
        status, body, seconds, error = result
        rec["requests"].append({"url": url, "status": status, "seconds": seconds,
                                "error": error, "bytes": len(body),
                                "body_sha256": hashlib.sha256(body).hexdigest() if body else None})
        return result

    st, body, secs, err = fetch(base + "robots.txt")
    rec["robots"] = {"status": st, "seconds": secs, "error": err, "bytes": len(body)}
    declared = []
    if st == 200 and body:
        text = body.decode("utf-8", "replace")
        declared = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", text)
    rec["robots"]["declares_sitemap"] = bool(declared)
    rec["robots"]["declared_sitemaps"] = declared[:5]

    sm_url = declared[0] if declared else urljoin(base, "/sitemap.xml")
    st, body, secs, err = fetch(sm_url)
    kind, count, lastmods = parse_sitemap(body) if st == 200 else (None, 0, [])
    rec["sitemap"] = {"url": sm_url, "from_robots": bool(declared), "status": st,
                      "seconds": secs, "error": err, "bytes": len(body),
                      "parsed_kind": kind, "entries": count,
                      "entries_with_lastmod": len(lastmods),
                      "youngest_lastmod_days": age_days(lastmods)}

    st, body, secs, err = fetch(base)
    rec["homepage"] = {"status": st, "seconds": secs, "error": err, "bytes": len(body)}
    links = FeedLinks()
    if st == 200 and body:
        links.feed(body.decode("utf-8", "replace"))
    candidates = [(urljoin(base, href), True) for href in links.links]
    candidates += [(urljoin(base, path), False) for path in CONVENTIONAL_FEEDS]
    rec["feed_autodiscovered"] = False
    rec["feed"] = {"url": None, "autodiscovered": False, "status": None,
                   "seconds": None, "error": "no supported feed found by this probe",
                   "parsed_kind": None, "items": 0, "youngest_item_days": None}
    seen = set()
    for feed_url, discovered in candidates:
        if feed_url in seen:
            continue
        seen.add(feed_url)
        st, body, secs, err = fetch(feed_url)
        kind, items, dates = parse_feed(body) if st == 200 else (None, 0, [])
        if kind in ("rss", "atom", "rss1"):
            rec["feed_autodiscovered"] = discovered
            rec["feed"] = {"url": feed_url, "autodiscovered": discovered,
                           "status": st, "seconds": secs, "error": err,
                           "parsed_kind": kind, "items": items,
                           "youngest_item_days": age_days(dates)}
            break
    return rec

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("seeds_path")
    parser.add_argument("out_path")
    parser.add_argument("--timeout", type=float, default=TIMEOUT)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    seeds_path, out_path = args.seeds_path, args.out_path
    seeds = []
    from pathlib import Path
    for line in Path(seeds_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        cat, _, dom = line.partition(":")
        dom = dom.strip()
        if not cat or not dom or any(c in dom for c in "/ :?#"):
            parser.error("invalid category:domain seed")
        seeds.append((cat, dom))
    if not seeds:
        parser.error("seed list is empty")
    started = datetime.now(timezone.utc).isoformat()
    results = []
    def save(complete):
        payload = {"run_started_utc": started,
                   "run_finished_utc": datetime.now(timezone.utc).isoformat() if complete else None,
                   "seed_count": len(seeds), "completed_count": len(results), "complete": complete,
                   "user_agent": UA, "timeout_s": args.timeout, "rig_version": "1.1",
                   "results": results}
        target = Path(out_path)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(target)
    for i, (cat, dom) in enumerate(seeds, 1):
        r = probe(dom, timeout=args.timeout)
        r["category"] = cat
        results.append(r)
        save(False)
        print(f"[{i}/{len(seeds)}] {dom:34s} robots={r['robots']['status']} "
              f"sitemap={r['sitemap']['status']}/{r['sitemap']['entries']} "
              f"feed={r['feed']['parsed_kind']}", file=sys.stderr, flush=True)
        time.sleep(0.4)
    save(True)
    print(f"wrote {out_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
