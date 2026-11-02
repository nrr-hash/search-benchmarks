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

def require(condition, message):
    if not condition:
        raise ValueError(message)

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
    require(analysis.summarise(run)==summary, 'summary differs from run')
    require(run['complete'] and len(run['results'])==60, 'repository verification failed')
    require(run['seed_sha256']==hashlib.sha256((ROOT/'dead-web/seeds.txt').read_bytes()).hexdigest(), 'repository verification failed')
    require(run['script_sha256']==hashlib.sha256((ROOT/'dead-web/deadtech_bench.py').read_bytes()).hexdigest(), 'repository verification failed')
    evidence=json.loads(gzip.decompress((ROOT/'dead-web/results/evidence_2026-11-02.json.gz').read_bytes()))['records']
    for entry in evidence:
        row=next(row for row in run['results'] if row['domain']==entry['domain'])
        selected=row[entry['endpoint']]
        require(selected['parsed_kind']==entry['parsed_kind'], 'repository verification failed')
        require(selected['entries' if entry['endpoint']=='sitemap' else 'items']==entry['element_count'], 'repository verification failed')
        require(any(req['body_sha256']==entry['body_sha256'] and req['url']==entry['url'] for req in row['requests']), 'repository verification failed')
    landing=(ROOT/'docs/index.html').read_text()
    advertisement=json.loads((ROOT/'ad-audit/results/job_2026-11-02.json').read_text())
    require(f"{summary['counts']['either']} supplied" in landing, 'landing detection count stale')
    require(f"{summary['requests_recorded']} recorded requests" in landing, 'landing request count stale')
    require(f"{advertisement['words']} counted words" in landing, 'landing word count stale')
    docs=ROOT/'docs';pages=list(docs.rglob('*.html'));external=set()
    for page in pages:
        source=page.read_text();parser=Links();parser.feed(source)
        require(parser.h1==1, f'{page}: expected one h1')
        require(len(parser.ids)==len(set(parser.ids)), f'{page}: duplicate IDs')
        for href in parser.links:
            parsed=urlparse(href)
            if parsed.scheme in ('http','https'):
                external.add(href)
                if href.startswith('https://github.com/nrr-hash/search-benchmarks/blob/main/'):
                    require((ROOT/unquote(parsed.path.split('/blob/main/',1)[1])).is_file(), href)
                continue
            require(not parsed.scheme or parsed.scheme=='mailto', href)
            if parsed.scheme=='mailto':continue
            target=(page.parent/unquote(parsed.path)).resolve() if parsed.path else page
            if target.is_dir():target=target/'index.html'
            require(target.is_file(), (page,href))
            if parsed.fragment:
                p=Links();p.feed(target.read_text());require(parsed.fragment in p.ids, (page,href))
    for path in ('index.html','magnifying-glass/index.html','dead-web/index.html'):
        require((docs/path).is_file(), 'published URL path removed')
    files=sorted(docs.rglob('*.html'))+[ROOT/'dead-web/results/summary_2026-11-02.json']
    before={str(p):p.read_bytes() for p in files}
    subprocess.run([sys.executable,str(ROOT/'tools/build_articles.py')],check=True)
    require(all(p.read_bytes()==before[str(p)] for p in files), 'article generation is not reproducible')
    print(json.dumps({'status':'PASS','pages':len(pages),'external_links':sorted(external)},indent=2))

if __name__=='__main__':main()
