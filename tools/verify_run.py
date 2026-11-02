"""Verify every archived decoded body against its recorded hash, then reparse selections."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bench',ROOT/'dead-web/deadtech_bench.py')
bench=importlib.util.module_from_spec(spec);spec.loader.exec_module(bench)

def verify(path):
    path=Path(path);data=json.loads(path.read_text())
    if not data.get('complete') or len(data['results']) != data['seed_count']:
        raise ValueError('incomplete run')
    bodies=0
    for row in data['results']:
        for request in row['requests']:
            if request['bytes']:
                relative=Path(request['body_file'])
                if relative.is_absolute() or '..' in relative.parts:
                    raise ValueError('invalid body path')
                body=gzip.decompress((path.parent/relative).read_bytes())
                assert len(body)==request['bytes'], 'body size mismatch'
                assert hashlib.sha256(body).hexdigest()==request['body_sha256'], 'body hash mismatch'
                bodies+=1
        for field,parser,count_key in [('sitemap',bench.parse_sitemap,'entries'),('feed',bench.parse_feed,'items')]:
            endpoint=row[field]
            if endpoint.get('status')==200 and endpoint.get('url'):
                requests=[r for r in row['requests'] if r['url']==endpoint['url'] and r['status']==200 and r.get('body_file')]
                if not requests:
                    raise ValueError('selected response missing from archive')
                body=gzip.decompress((path.parent/requests[-1]['body_file']).read_bytes())
                kind,count,dates=parser(body)
                assert (kind,count)==(endpoint['parsed_kind'],endpoint[count_key]), 'parsed result mismatch'
    return {'domains':len(data['results']),'body_references_verified':bodies,'status':'PASS'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('run');args=parser.parse_args()
    print(json.dumps(verify(args.run)))
