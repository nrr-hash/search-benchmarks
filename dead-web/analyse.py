#!/usr/bin/env python3
"""Summarise a dated probe run; --json emits the same data used by the article."""
import argparse
import json
import math
from pathlib import Path
import statistics


def sitemap_ok(row):
    sm = row['sitemap']
    return sm['status'] == 200 and sm['parsed_kind'] in ('urlset', 'sitemapindex')


def feed_ok(row):
    feed = row['feed']
    return feed.get('status') == 200 and feed['parsed_kind'] in ('rss', 'atom', 'rss1')


def latency(rows, key):
    values = sorted(row[key]['seconds'] for row in rows
                    if row[key].get('status') == 200 and row[key].get('seconds') is not None)
    return {'n': len(values), 'median_s': statistics.median(values) if values else None,
            'p90_s': values[math.ceil(.9*len(values))-1] if values else None,
            'definition': 'successful selected endpoint probe elapsed time; nearest-rank p90'}


def summarise(data):
    rows = data['results']
    if len({row['domain'] for row in rows}) != len(rows):
        raise ValueError('duplicate result domains')
    if data.get('complete') and data.get('seed_count') != len(rows):
        raise ValueError('complete run has missing results')
    counts = {
        'robots_200': sum(r['robots']['status'] == 200 for r in rows),
        'declares_sitemap': sum(bool(r['robots']['declares_sitemap']) for r in rows),
        'sitemap': sum(sitemap_ok(r) for r in rows),
        'populated_sitemap': sum(sitemap_ok(r) and r['sitemap']['entries'] > 0 for r in rows),
        'feed': sum(feed_ok(r) for r in rows),
        'autodiscovered_feed': sum(feed_ok(r) and r['feed']['autodiscovered'] for r in rows),
        'either': sum(sitemap_ok(r) or feed_ok(r) for r in rows),
    }
    counts['neither_found'] = len(rows) - counts['either']
    requests = [req for row in rows for req in row.get('requests', [])]
    categories = {}
    for row in rows:
        category = categories.setdefault(row['category'], {'n': 0, 'either': 0})
        category['n'] += 1
        category['either'] += int(sitemap_ok(row) or feed_ok(row))
    return {'run_started_utc': data['run_started_utc'], 'run_finished_utc': data['run_finished_utc'],
            'rig_version': data.get('rig_version', '1.0'), 'n': len(rows),
            'complete': data.get('complete'), 'counts': counts, 'categories': categories,
            'requests_recorded': len(requests),
            'request_errors': sum(bool(req.get('error')) for req in requests),
            'deadline_failures': sum(req.get('error') == 'deadline exceeded' for req in requests),
            'latency': {key: latency(rows, key) for key in ('robots','sitemap')},
            'limits': ['Rates describe the fixed seed list and this probe only.',
                       'Recognised XML roots do not validate inventory completeness or linked URLs.',
                       'Elapsed times include client processing and redirects; v1.2 includes worker startup.',
                       'Cross-version observations are not a controlled time series.']}


def main(path, as_json=False):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    summary = summarise(data)
    if as_json:
        print(json.dumps(summary, indent=2))
        return
    print(f"run {summary['run_started_utc']} to {summary['run_finished_utc']} | rig {summary['rig_version']}")
    print(f"observed domains {summary['n']} | complete={summary['complete']}")
    for label, count in summary['counts'].items():
        n = summary['n']
        rate = f'{100*count/n:.1f}%' if n else 'N/A'
        print(f'{label:24} {count}/{n} ({rate})')
    for key, stats in summary['latency'].items():
        print(f'{key} successful elapsed time: {stats}')
    print('No historical v1.0 freshness summary: timestamps were scanned incompletely.')
    print(f"request errors: {summary['request_errors']}/{summary['requests_recorded']} recorded attempts")
    print('categories:', json.dumps(summary['categories'], sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    try:
        main(args.run, args.json)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.error(str(error))
