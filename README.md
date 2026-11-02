# web-measurement-rigs

Two small, reproducible measurement rigs and the write-ups built on them.

Both are standard-library Python 3.10+. No dependencies, no virtualenv, no
model inside, no detector, no score. The measurement rigs produce JSON; the analyser prints a text summary. Published availability figures can be recomputed from the dated JSON. The historical freshness summary is withdrawn.

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

The hash refers to the exact original UTF-8 bytes. Rig v1.1 preserves line endings when hashing. Matching bytes reproduce core counts; Unicode metadata additionally depends on the recorded Unicode database version. A different hash means you are
measuring a different document, and the numbers should differ.

## dead-web

```
cd dead-web
python3 deadtech_bench.py seeds.txt runs/out.json
python3 analyse.py runs/out.json
```

For each domain in the seed list, over plain HTTPS: fetch `robots.txt` and
look for a `Sitemap:` directive; fetch the first declared sitemap or
`/sitemap.xml`; parse and count entries and `lastmod` values; fetch the
homepage and look for RSS/Atom autodiscovery, falling back to six
conventional feed paths; fetch and parse RSS 2.0, RSS 1.0, or Atom feeds, retaining every explicit probe attempt.

Single threaded, 0.4s between domains, configurable 15s socket timeout, no explicit retries, nothing
imputed. Failures are recorded as failures. The 60-domain run takes about six
minutes.

`seeds.txt` was fixed before any measurement was taken. It is hand-picked for
category spread: 12 categories, 5 domains each. It is **not** a random or
traffic-ranked sample, and no percentage derived from it describes the web.

`runs/run_2026-10-31.json` is the run behind the published piece. Re-running
will not reproduce it exactly, because the web changes. The dated JSON is historical v1.0 evidence. Current v1.1 code changes the method as well as observing a changing web. Its freshness estimates are withdrawn from the write-up because the original rig inspected only a prefix of the dates. Do not interpret cross-version differences as web changes alone.

## Provenance

The scripts were generated with AI assistance against specifications I wrote,
then read, run and checked by me. The seed list, the method and the
limitations are mine. Neither piece has been through independent review, and
both say so.

Written and published by Nathaniel Robertson, October 2026.

## Licence

MIT, see `LICENSE`. The write-up prose in `docs/` is &copy; Nathaniel
Robertson 2026, all rights reserved; the code is MIT.

## Verification

Run `python3 -m unittest discover -s tests -v`. CI runs the suite on Python 3.10 and 3.13. No source advertisement or historical response bodies are included, so full historical source verification remains unavailable.

Historical v1.0 source: [commit 5979074](https://github.com/nrr-hash/search-benchmarks/tree/597907474d04ed5d9fbe0e8ccf62a2f0a4dbc45c). Run metadata and body hashes improve provenance in v1.1, but response bodies are not archived and a publisher timestamp does not verify content freshness. Socket timeouts are not a total run deadline.
