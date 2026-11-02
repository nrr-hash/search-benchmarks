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

def read_body(root, request):
    relative = Path(request['body_file'])
    target = (root / relative).resolve()
    if relative.is_absolute() or '..' in relative.parts or not target.is_relative_to(root.resolve()):
        raise ValueError('invalid body path')
    body = gzip.decompress(target.read_bytes())
    if len(body) != request['bytes']:
        raise ValueError('body size mismatch')
    if hashlib.sha256(body).hexdigest() != request['body_sha256']:
        raise ValueError('body hash mismatch')
    return body

def verify(path):
    path=Path(path);data=json.loads(path.read_text())
    rows = data['results']
    if not data.get('complete') or len(rows) != data['seed_count']:
        raise ValueError('incomplete run')
    if len({row['domain'] for row in rows}) != len(rows):
        raise ValueError('duplicate result domains')
    bodies=0
    for row in rows:
        for request in row['requests']:
            if request['bytes']:
                read_body(path.parent, request)
                bodies+=1
        for field,parser,count_key in [('sitemap',bench.parse_sitemap,'entries'),('feed',bench.parse_feed,'items')]:
            endpoint=row[field]
            if endpoint.get('status')==200 and endpoint.get('url'):
                requests=[r for r in row['requests'] if r['url']==endpoint['url'] and r['status']==200 and r.get('body_file')]
                if not requests:
                    raise ValueError('selected response missing from archive')
                body=read_body(path.parent, requests[-1])
                kind,count,dates=parser(body)
                if (kind,count)!=(endpoint['parsed_kind'],endpoint[count_key]):
                    raise ValueError('parsed result mismatch')
    return {'domains':len(rows),'body_references_verified':bodies,'status':'PASS'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('run');args=parser.parse_args()
    print(json.dumps(verify(args.run)))
