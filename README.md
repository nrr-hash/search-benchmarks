# Search benchmarks

Two inspectable research pitches, with dated measurements, code, and limits.
The published addresses are permanent:

- [Measurement rigs](https://nrr-hash.github.io/search-benchmarks/)
- [The magnifying glass problem](https://nrr-hash.github.io/search-benchmarks/magnifying-glass/)
- [What the dead web still publishes](https://nrr-hash.github.io/search-benchmarks/dead-web/)

## Publisher-text audit

The current article measures SearchApi's Technical Researcher / Writer vacancy,
selected by job ID from the publisher's public Ashby feed. It uses the exact
`descriptionPlain` value encoded as UTF-8, without trimming or line-ending
normalisation. The source URLs, retrieval time, response hash, input hash, script
hash, Python version, and Unicode version are recorded in
`ad-audit/results/job_2026-11-02.json`.

```sh
python3 ad-audit/measure_job.py new-job-report.json
```

To measure your own UTF-8 document:

```sh
python3 ad-audit/audit_rig.py input.txt > report.json
```

Counts use declared heuristics. Words are ASCII-letter/digit regex matches;
sentences are heuristic segments; symbol ranges are neither a complete emoji
inventory nor grapheme segmentation. Pattern counts are not an AI detector.

The publisher's text is not redistributed. The endpoint can change; a matching
input hash is necessary before comparing counts. The October pasted-copy report
is retained separately as historical output, not as evidence about the current
publisher text. Its original input is unavailable.

## Sitemap and feed probe

The current article uses `dead-web/runs/run_2026-11-02_v1_2.json`, a completed
60-domain run. Reproduce the procedure from the repository root:

```sh
python3 dead-web/deadtech_bench.py dead-web/seeds.txt new-run.json --timeout 6 --workers 8 --pause 0.4
python3 dead-web/analyse.py new-run.json --json
python3 tools/verify_run.py new-run.json
```

Use a new output filename: the rig refuses to overwrite an existing run.
Python 3.10+ and its standard library are sufficient. No API key is required.

The method fetches robots.txt, tries up to five declared sitemaps then the
conventional fallback, and stops at the first recognised sitemap root. It fetches
the homepage and tries up to ten declared RSS/Atom links, then six conventional
paths, stopping at the first recognised RSS 2.0, RSS 1.0, or Atom feed. Sitemap
indexes are not traversed. Counts are XML-element counts, not verified live URLs.

Requests within each domain are sequential and paced. Concurrency, pacing, and
a hard elapsed deadline per request are explicit. Redirects are followed by
urllib; the final URL is recorded where available. The request ledger records
every explicit probe attempt, including errors. Timings include subprocess
startup, DNS, redirects, transfer, and decompression; they are not server-response
benchmarks. A 10 MB cap applies separately to downloaded and decoded bytes.

The CLI saves decoded response bodies to a sibling `bodies/` directory for local
verification. Those third-party page/feed contents are not redistributed here;
`body_file` values in the dated run identify those local captures. Public outputs
include body hashes, the request ledger, a computed summary, and extracted
parser evidence in `dead-web/results/` (gzip-compressed JSON). `verify_run.py` requires the local bodies
from the same run. `tools/check_repository.py` verifies the public outputs without
them. Neither tool establishes that publisher timestamps reflect actual changes.

The seed list is fixed, hand-picked across twelve categories, and not a random
or traffic-ranked sample. Rates describe only this list and probe. A deadline or
failed request is not proof of absence or bot blocking. The earlier v1.0 run is
retained as historical data; different methods prevent a controlled time-series
comparison. Its incomplete timestamp scan is not used for freshness conclusions.

## Build and verification

```sh
python3 tools/build_articles.py
python3 tools/embed_code.py
python3 -m unittest discover -s tests -v
python3 tools/check_repository.py
```

The article builder reads the dated reports to insert the published measurements;
embedded scripts carry matching SHA-256 labels. CI runs the regression suite and
repository checks on Python 3.10 and 3.13. Tests include a local HTTP redirect and
request-worker integration check. Network surveys are deliberate runs, not part
of CI.

## Provenance and licence

Written by Nathaniel Robertson. Scripts and revisions use AI assistance. Automated
checks and model-run source checks are not independent human editorial sign-off.
The source hashes identify measured bytes, not authorship or truth.

Code is MIT licensed; see `LICENSE`. Article prose in `docs/` is © Nathaniel
Robertson 2026, all rights reserved. Dated measurements are provided for inspection
and comparison within the limits described above.
