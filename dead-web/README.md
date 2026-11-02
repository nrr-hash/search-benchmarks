# Sitemap and feed probe

Run from the repository root using the commands in the main README. Rig v1.2
records all explicit attempts, bounds request elapsed time and body sizes,
resolves relative feed links against the final homepage URL and HTML base,
and recognises sitemap roots plus RSS 2.0, RSS 1.0, and Atom.

The current completed run is `runs/run_2026-11-02_v1_2.json`. Its derived outputs
are in `results/`. Raw decoded bodies are local captures, not repository files;
`tools/verify_run.py` checks them when available. Public-output consistency is
checked by `tools/check_repository.py`.

A recognised XML root is not a validation of a populated, accurate, or complete
inventory. Sitemap indexes are not traversed. Missing endpoints are reported as
not found by this bounded probe. Timeouts and HTTP failures do not establish a
site's policy. Timestamp parsing cannot verify actual content freshness.

The 31 October run remains historical v1.0 data. It uses a different method and
its incomplete freshness estimates are not used in the current article.
