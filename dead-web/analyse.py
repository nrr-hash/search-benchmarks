#!/usr/bin/env python3
"""
analyse.py - summarise a deadtech_bench.py run.

Usage:  python3 analyse.py runs/run_2026-10-31.json

Prints the headline rates, latency, freshness, failures, and a per-category
breakdown. Every figure in the published write-up comes from this file.
"""
import json, statistics, sys

def sitemap_ok(r):
    return r["sitemap"]["status"] == 200 and r["sitemap"]["parsed_kind"] in ("urlset", "sitemapindex")

def feed_ok(r):
    return r["feed"]["parsed_kind"] in ("rss", "atom", "rss1")

def main(path):
    from pathlib import Path
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    R = d["results"]
    n = len(R)
    def rate(label, c):
        print(f"{label:<34} {c:>3}/{n}  ({(100*c/n if n else 0):5.1f}%)")

    print(f"run started  {d['run_started_utc']}")
    print(f"run finished {d['run_finished_utc']}")
    print(f"seeds        {n}\n")

    rate("robots.txt returned 200", sum(1 for r in R if r["robots"]["status"] == 200))
    rate("robots.txt declares a sitemap", sum(1 for r in R if r["robots"]["declares_sitemap"]))
    rate("sitemap parses", sum(1 for r in R if sitemap_ok(r)))
    rate("feed parses", sum(1 for r in R if feed_ok(r)))
    rate("feed autodiscovered from homepage", sum(1 for r in R if r["feed"]["autodiscovered"]))
    either = sum(1 for r in R if sitemap_ok(r) or feed_ok(r))
    rate("EITHER sitemap or feed", either)
    rate("NEITHER", n - either)

    for key in ("robots", "sitemap"):
        lat = sorted(r[key]["seconds"] for r in R
                     if r[key]["status"] == 200 and r[key]["seconds"] is not None)
        if lat:
            import math
            print(f"{key} latency median {statistics.median(lat):.3f}s "
                  f"p90 {lat[max(0, math.ceil(.9*len(lat))-1)]:.3f}s n={len(lat)}")
        else:
            print(f"{key} latency unavailable n=0")

    if d.get("rig_version") == "1.1":
        for key, field in (("sitemap", "youngest_lastmod_days"), ("feed", "youngest_item_days")):
            ages = [r[key][field] for r in R if r[key].get(field) is not None]
            if ages:
                print(f"youngest {key} timestamp median {statistics.median(ages):.2f} days n={len(ages)}")
    else:
        print("Historical v1.0 freshness summary withdrawn: incomplete timestamp scan.")

    print("\nfailures and refusals:")
    for r in R:
        if r["robots"]["status"] != 200:
            print(f"  {r['domain']:<32} robots={r['robots']['status']}  {r['robots']['error']}")

    print("\nby category (either available):")
    cats = {}
    for r in R:
        c = cats.setdefault(r["category"], [0, 0])
        c[1] += 1
        c[0] += sitemap_ok(r) or feed_ok(r)
    for c, (a, b) in sorted(cats.items(), key=lambda x: (-x[1][0]/x[1][1], x[0])):
        print(f"  {c:<14} {a}/{b}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "runs/run_2026-10-31.json")
