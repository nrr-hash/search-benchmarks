"""Offline checks of published paths, links, derived evidence, and generated output."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse,unquote
import gzip
import hashlib
import importlib.util
import json
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=[];self.h1=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if attrs.get('id'):self.ids.append(attrs['id'])
        if tag=='a' and attrs.get('href'):self.links.append(attrs['href'])
        if tag=='h1':self.h1+=1

def main():
    analysis=load('analysis','dead-web/analyse.py')
    run=json.loads((ROOT/'dead-web/runs/run_2026-11-02_v1_2.json').read_text())
    summary=json.loads((ROOT/'dead-web/results/summary_2026-11-02.json').read_text())
    assert analysis.summarise(run)==summary,'summary differs from run'
    assert run['complete'] and len(run['results'])==60
    assert run['seed_sha256']==hashlib.sha256((ROOT/'dead-web/seeds.txt').read_bytes()).hexdigest()
    assert run['script_sha256']==hashlib.sha256((ROOT/'dead-web/deadtech_bench.py').read_bytes()).hexdigest()
    evidence=json.loads(gzip.decompress((ROOT/'dead-web/results/evidence_2026-11-02.json.gz').read_bytes()))['records']
    for entry in evidence:
        row=next(row for row in run['results'] if row['domain']==entry['domain'])
        selected=row[entry['endpoint']]
        assert selected['parsed_kind']==entry['parsed_kind']
        assert selected['entries' if entry['endpoint']=='sitemap' else 'items']==entry['element_count']
        assert any(req['body_sha256']==entry['body_sha256'] and req['url']==entry['url'] for req in row['requests'])
    docs=ROOT/'docs';pages=list(docs.rglob('*.html'));external=set()
    for page in pages:
        source=page.read_text();parser=Links();parser.feed(source)
        assert parser.h1==1,f'{page}: expected one h1'
        assert len(parser.ids)==len(set(parser.ids)),f'{page}: duplicate IDs'
        for href in parser.links:
            parsed=urlparse(href)
            if parsed.scheme in ('http','https'):
                external.add(href)
                if href.startswith('https://github.com/nrr-hash/search-benchmarks/blob/main/'):
                    assert (ROOT/unquote(parsed.path.split('/blob/main/',1)[1])).is_file(),href
                continue
            assert not parsed.scheme or parsed.scheme=='mailto',href
            if parsed.scheme=='mailto':continue
            target=(page.parent/unquote(parsed.path)).resolve() if parsed.path else page
            if target.is_dir():target=target/'index.html'
            assert target.is_file(),(page,href)
            if parsed.fragment:
                p=Links();p.feed(target.read_text());assert parsed.fragment in p.ids,(page,href)
    for path in ('index.html','magnifying-glass/index.html','dead-web/index.html'):
        assert (docs/path).is_file(),'published URL path removed'
    files=sorted(docs.rglob('*.html'))+[ROOT/'dead-web/results/summary_2026-11-02.json']
    before={str(p):p.read_bytes() for p in files}
    subprocess.run([sys.executable,str(ROOT/'tools/build_articles.py')],check=True)
    assert all(p.read_bytes()==before[str(p)] for p in files),'article generation is not reproducible'
    print(json.dumps({'status':'PASS','pages':len(pages),'external_links':sorted(external)},indent=2))

if __name__=='__main__':main()
