# web-measurement-rigs

Two small, reproducible measurement rigs and the write-ups built on them.

Both are standard-library Python 3.10+. No dependencies, no virtualenv, no
model inside, no detector, no score. Each prints JSON, and every figure in the
published write-ups is read back out of that JSON rather than typed by hand.

Published write-ups:

- **The magnifying glass problem** &mdash; `docs/magnifying-glass/`
  A Unicode and pattern audit of a job advertisement arguing that its author
  can tell real research from AI slop.
- **What the dead web still publishes** &mdash; `docs/dead-web/`
  60 domains measured for sitemap and feed availability, latency and freshness.

## ad-audit

```
cd ad-audit
python3 audit_rig.py path/to/text.txt > results.json
```

Takes any plain-text file. Returns character, word and sentence counts,
sentence-length dispersion, a full Unicode breakdown of every emoji codepoint
(name, block, UTF-8 and UTF-16 width, ASCII fallback, normalisation
behaviour), and counts of surface constructions commonly listed as
machine-writing tells.

The tell list is mine and is not validated against a labelled corpus. A count
is a description, not a detector. Nothing this script prints identifies an
author, and the write-up says so at length.

`results/ad_results.json` is the run behind the published piece.

**The measured text is not in this repository.** It is a third party's
copyrighted advertisement, quoted only in fragments in the write-up. To
reproduce the exact numbers, save the advertisement's plain text and check it
against the hash the write-up publishes:

```
sha256sum searchapi_ad.txt
# 6b873986a8e18d34f4e448665721d0b332de9bdb2058db4ffc4be99ed84347da
```

A matching hash gives identical output. A different hash means you are
measuring a different document, and the numbers should differ.

## dead-web

```
cd dead-web
python3 deadtech_bench.py seeds.txt runs/out.json
python3 analyse.py runs/out.json
```

For each domain in the seed list, over plain HTTPS: fetch `robots.txt` and
look for a `Sitemap:` directive; fetch the declared sitemap or
`/sitemap.xml`; parse and count entries and `lastmod` values; fetch the
homepage and look for RSS/Atom autodiscovery, falling back to six
conventional feed paths; fetch and parse the feed.

Single threaded, 0.4s between domains, 15s timeout, nothing retried, nothing
imputed. Failures are recorded as failures. The 60-domain run takes about six
minutes.

`seeds.txt` was fixed before any measurement was taken. It is hand-picked for
category spread: 12 categories, 5 domains each. It is **not** a random or
traffic-ranked sample, and no percentage derived from it describes the web.

`runs/run_2026-10-31.json` is the run behind the published piece. Re-running
will not reproduce it exactly, because the web changes. That is the point of
keeping dated runs rather than one overwritten result.

## Provenance

The scripts were generated with AI assistance against specifications I wrote,
then read, run and checked by me. The seed list, the method and the
limitations are mine. Neither piece has been through independent review, and
both say so.

Written and published by Nathaniel Robertson, October 2026.

## Licence

MIT, see `LICENSE`. The write-up prose in `docs/` is &copy; Nathaniel
Robertson 2026, all rights reserved; the code is MIT.
