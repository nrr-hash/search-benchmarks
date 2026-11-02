#!/usr/bin/env python3
"""Measure publisher-provided descriptionPlain, without HTML-to-text reconstruction.

Usage: python3 ad-audit/measure_job.py output.json
The copyrighted input is fetched for analysis, not redistributed in this repository.
"""
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = "https://api.ashbyhq.com/posting-api/job-board/SearchApi"
JOB_ID = "5202d0e3-e0c4-4a77-82e2-a8982f270de3"
JOB_URL = "https://www.searchapi.io/careers?ashby_jid=" + JOB_ID

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def select_input(raw):
    data = json.loads(raw)
    jobs = [j for j in data["jobs"] if j.get("id") == JOB_ID]
    if len(jobs) != 1 or not isinstance(jobs[0].get("descriptionPlain"), str):
        raise ValueError("expected exactly one job with descriptionPlain")
    return jobs[0]["descriptionPlain"].encode("utf-8")

def measure(raw, fetched_at):
    source = select_input(raw)
    rig = load("audit_rig", HERE / "audit_rig.py")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "description.txt"
        path.write_bytes(source)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rig.main(path)
    report = json.loads(output.getvalue())
    report["provenance"] = {
        "job_url": JOB_URL, "api_url": SOURCE, "job_id": JOB_ID,
        "fetched_at_utc": fetched_at, "api_response_sha256": hashlib.sha256(raw).hexdigest(),
        "extraction": "JSON jobs item with matching id; descriptionPlain encoded as UTF-8; no trimming or normalisation",
        "audit_script_sha256": hashlib.sha256((HERE / "audit_rig.py").read_bytes()).hexdigest(),
        "python_version": sys.version,
        "scope": "publisher-provided plain text at retrieval; not the October pasted copy or a browser rendering",
    }
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output")
    args = parser.parse_args()
    path = Path(args.output)
    if path.exists():
        parser.error("output exists; choose a new path")
    bench = load("source_fetch", ROOT / "dead-web/deadtech_bench.py")
    status, raw, seconds, error = bench.get(SOURCE, timeout=30)
    if status != 200 or error:
        parser.error(f"source fetch failed: {status} {error}")
    report = measure(raw, datetime.now(timezone.utc).isoformat())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}", file=sys.stderr)

if __name__ == "__main__":
    main()
