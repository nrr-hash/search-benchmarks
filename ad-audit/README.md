# Publisher-text audit

`measure_job.py` fetches the public job-board API linked from the supplied careers
page, selects the exact job ID, and measures its `descriptionPlain` field.
`results/job_2026-11-02.json` records the current article's counts and provenance.
The source text itself is not redistributed. Later responses may change; compare
hashes before comparing counts.

`audit_rig.py` measures any UTF-8 file. It hashes original bytes and exposes its
word, sentence, and symbol-range heuristics. Its surface patterns are not
validated authorship indicators. No output is an AI detector or quality score.

`results/ad_results.json` is historical output over a different pasted copy,
whose original bytes are unavailable. It is not used to describe the current
publisher-provided text. See the main README for commands and limits.
