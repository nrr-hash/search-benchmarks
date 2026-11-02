# dead-web

Does the declared, free, machine-readable web still work?

See the repository README for usage. Two things worth repeating here:

1. `seeds.txt` is fixed and hand-picked, not sampled. Percentages describe
   this list of 60 domains and nothing wider.
2. Where a domain serves a `sitemapindex`, the `entries` figure counts child
   sitemaps, not URLs. The script does not recurse. The published write-up
   says so; if you build on this, that is the first thing to fix.

Known gaps, unfixed on purpose so they are visible rather than buried:

- The published observations are one historical v1.0 run, not a time series or variance estimate.
- The user-agent is not negotiated with any site, so some 403s are bot
  defence rather than policy.
- Historical v1.0 freshness values inspected only date prefixes and are withdrawn from the write-up. v1.1 inspects every supplied date, excludes placeholders and future dates, and supports ISO and email formats.
- A sitemap that parses is not a sitemap that is complete or correct. Checking
  declared URLs against reality is the obvious next experiment.
