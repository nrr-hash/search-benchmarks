#!/usr/bin/env python3
"""
deadtech_bench.py - does the declared, free, machine-readable web still work?

For every domain in a fixed seed list, this fetches, over plain HTTPS:
  1. /robots.txt                      -> present? does it declare Sitemap:?
  2. up to five declared sitemaps, then /sitemap.xml, stopping at first recognised root
  3. the homepage HTML                -> is an RSS/Atom feed autodiscovered?
  4. that feed                        -> does it parse, how many items, how fresh?

Records every explicit probe attempt, including failures. urllib follows redirects;
records include the final URL. Timings include worker startup, redirects, body
transfer, and decompression. No explicit retries or imputed observations.

Usage:  python3 deadtech_bench.py seeds.txt out.json [--timeout 15]

Standard library only. Domain concurrency is explicit; requests within a domain
are sequential and paced. The CLI archives decoded successful response bodies.
"""
import argparse, base64, hashlib, json, math, re, sys, time, gzip, io
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from email.utils import parsedate_to_datetime
import urllib.request, urllib.error
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET
from datetime import datetime, timezone

VERSION = "1.2"
UA = "deadtech-bench/1.2 (+https://nrr-hash.github.io/search-benchmarks/)"
TIMEOUT = 15

def _get_direct(url, timeout=TIMEOUT, limit=10_000_000, details=None):
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
            if details is not None:
                details.update(final_url=r.geturl(), content_type=r.headers.get("Content-Type"),
                               content_encoding=r.headers.get("Content-Encoding"))
            return r.status, body, round(time.monotonic() - t0, 3), None
    except urllib.error.HTTPError as e:
        if details is not None:
            details.update(final_url=e.geturl(), content_type=e.headers.get("Content-Type"))
        e.close()
        return e.code, b"", round(time.monotonic() - t0, 3), f"HTTPError {e.code}"
    except Exception as e:
        return None, b"", round(time.monotonic() - t0, 3), f"{type(e).__name__}: {str(e)[:120]}"

def get(url, timeout=TIMEOUT, limit=10_000_000, details=None):
    """One request, including automatic redirects, with a hard elapsed deadline.

    A subprocess bounds DNS, connection, reads, and decompression together.
    The returned seconds include worker startup; these are probe timings,
    not server response time or bare network latency.
    """
    started = time.monotonic()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        return None, b"", 0.0, "invalid HTTP(S) URL"
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--fetch-worker"],
            input=json.dumps({"url": url, "timeout": timeout, "limit": limit}),
            capture_output=True, text=True, timeout=timeout, check=True)
        record = json.loads(result.stdout)
        if details is not None:
            details.update(record["details"])
        return record["status"], base64.b64decode(record["body"]), round(time.monotonic()-started, 3), record["error"]
    except subprocess.TimeoutExpired:
        return None, b"", round(time.monotonic()-started, 3), "deadline exceeded"
    except (subprocess.SubprocessError, ValueError, OSError) as error:
        return None, b"", round(time.monotonic()-started, 3), f"request worker: {type(error).__name__}"


def fetch_worker():
    args = json.load(sys.stdin)
    details = {}
    status, body, seconds, error = _get_direct(**args, details=details)
    json.dump({"status": status, "body": base64.b64encode(body).decode("ascii"),
               "error": error, "details": details}, sys.stdout)


class FeedLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.base = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "base" and a.get("href") and self.base is None:
            self.base = a["href"]
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
    if root.tag in ("{http://www.w3.org/2005/Atom}feed", "feed"):
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
        except (ValueError, OverflowError):
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

def probe(domain, timeout=TIMEOUT, archive=None, pause=0.2):
    base = f"https://{domain}/"
    rec = {"domain": domain, "requests": []}
    def fetch(url):
        if rec["requests"] and pause:
            time.sleep(pause)
        details = {}
        if archive is None:
            result = get(url, timeout=timeout)
        else:
            result = get(url, timeout=timeout, details=details)
        status, body, seconds, error = result
        rec["requests"].append({"url": url, "status": status, "seconds": seconds,
                                "error": error, "bytes": len(body),
                                "body_sha256": hashlib.sha256(body).hexdigest() if body else None})
        rec["requests"][-1].update(details)
        if archive is not None and body:
            digest = hashlib.sha256(body).hexdigest()
            target = Path(archive) / (digest + ".xml.gz")
            target.parent.mkdir(parents=True, exist_ok=True)
            # Content-addressed decoded response bytes, gzip mtime fixed for stable archives.
            target.write_bytes(gzip.compress(body, mtime=0))
            rec["requests"][-1]["body_file"] = "bodies/" + target.name
        return result

    st, body, secs, err = fetch(base + "robots.txt")
    rec["robots"] = {"status": st, "seconds": secs, "error": err, "bytes": len(body)}
    declared = []
    if st == 200 and body:
        text = body.decode("utf-8", "replace")
        declared = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", text)
    rec["robots"]["declares_sitemap"] = bool(declared)
    rec["robots"]["declared_sitemaps"] = declared
    rec["robots"]["sitemaps_omitted"] = max(0, len(declared) - 5)

    sitemap_candidates = list(dict.fromkeys(declared[:5] + [urljoin(base, "/sitemap.xml")]))
    rec["sitemap"] = {"url": None, "from_robots": False, "status": None, "seconds": None,
                      "error": "no recognised sitemap found", "bytes": 0, "parsed_kind": None,
                      "entries": 0, "entries_with_lastmod": 0, "youngest_lastmod_days": None}
    for sm_url in sitemap_candidates:
        st, body, secs, err = fetch(sm_url)
        kind, count, lastmods = parse_sitemap(body) if st == 200 else (None, 0, [])
        rec["sitemap"] = {"url": sm_url, "from_robots": sm_url in declared, "status": st,
                          "seconds": secs, "error": err, "bytes": len(body),
                          "parsed_kind": kind, "entries": count, "entries_with_lastmod": len(lastmods),
                          "youngest_lastmod_days": age_days(lastmods),
                          "entry_unit": "child_sitemaps" if kind == "sitemapindex" else "url_elements"}
        if kind in ("urlset", "sitemapindex"):
            break

    st, body, secs, err = fetch(base)
    rec["homepage"] = {"status": st, "seconds": secs, "error": err, "bytes": len(body)}
    links = FeedLinks()
    if st == 200 and body:
        links.feed(body.decode("utf-8", "replace"))
    final_home = rec["requests"][-1].get("final_url", base)
    document_base = urljoin(final_home, links.base) if links.base else final_home
    candidates = [(urljoin(document_base, href), True) for href in links.links[:10]]
    rec["feed_links_omitted"] = max(0, len(links.links) - 10)
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
    parser.add_argument("--timeout", type=float, default=TIMEOUT, help="hard per-request deadline in seconds")
    parser.add_argument("--workers", type=int, default=1, help="concurrent domains (1-8)")
    parser.add_argument("--pause", type=float, default=0.2, help="seconds between requests within each domain")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("timeout must be positive")
    if not 1 <= args.workers <= 8 or not math.isfinite(args.pause) or args.pause < 0:
        parser.error("workers must be 1-8 and pause must be non-negative and finite")
    seeds_path, out_path = args.seeds_path, args.out_path
    seeds = []
    seen = set()
    from pathlib import Path
    for line in Path(seeds_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        cat, _, dom = line.partition(":")
        dom = dom.strip()
        if not cat or not dom or any(c in dom for c in "/ :?#"):
            parser.error("invalid category:domain seed")
        dom = dom.lower()
        if dom in seen:
            parser.error("duplicate seed domain")
        seen.add(dom)
        seeds.append((cat, dom))
    if not seeds:
        parser.error("seed list is empty")
    started = datetime.now(timezone.utc).isoformat()
    results = []
    target = Path(out_path)
    if target.exists():
        parser.error("output exists; choose a new run path")
    target.parent.mkdir(parents=True, exist_ok=True)
    archive = target.parent / "bodies"
    def save(complete):
        payload = {"run_started_utc": started,
                   "run_finished_utc": datetime.now(timezone.utc).isoformat() if complete else None,
                   "seed_count": len(seeds), "completed_count": len(results), "complete": complete,
                   "user_agent": UA, "timeout_s": args.timeout, "rig_version": VERSION,
                   "workers": args.workers, "pause_s": args.pause,
                   "python_version": sys.version, "measurement_host": "execution environment; location unverified",
                   "seed_sha256": hashlib.sha256(Path(seeds_path).read_bytes()).hexdigest(),
                   "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   "results": results}
        target = Path(out_path)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(target)
    save(False)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {pool.submit(probe, dom, timeout=args.timeout, archive=archive, pause=args.pause): (cat, dom)
                   for cat, dom in seeds}
        for future in as_completed(pending):
            cat, dom = pending[future]
            r = future.result()
            r["category"] = cat
            results.append(r)
            results.sort(key=lambda item: next(i for i, (_, domain) in enumerate(seeds) if domain == item["domain"]))
            save(False)
            print(f"[{len(results)}/{len(seeds)}] {dom:34s} sitemap={r['sitemap']['parsed_kind']} "
                  f"feed={r['feed']['parsed_kind']}", file=sys.stderr, flush=True)
    save(True)
    print(f"wrote {out_path}", file=sys.stderr)

if __name__ == "__main__":
    if sys.argv[1:] == ["--fetch-worker"]:
        fetch_worker()
    else:
        main()
