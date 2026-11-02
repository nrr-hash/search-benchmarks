import contextlib
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
b = load('bench', 'dead-web/deadtech_bench.py')
a = load('audit', 'ad-audit/audit_rig.py')
z = load('analyse', 'dead-web/analyse.py')

class Rigs(unittest.TestCase):
    def test_all_sitemap_dates(self):
        self.assertEqual(b.age_days(['2000-01-01']*50+['2026-11-01'], datetime(2026,11,2,tzinfo=timezone.utc)),1)
    def test_all_feed_dates(self):
        body = '<rss><channel>'+''.join('<item><pubDate>2026-11-01</pubDate></item>' for _ in range(12))+'</channel></rss>'
        self.assertEqual(len(b.parse_feed(body)[2]),12)
    def test_invalid_dates(self):
        self.assertIsNone(b.age_days(['0001-01-01','2999-01-01','nonsense']))
    def test_html_attributes(self):
        links=b.FeedLinks();links.feed('<LINK REL="alternate" TYPE = "application/rss+xml" HREF = "/rss?a=1&amp;b=2">')
        self.assertEqual(links.links,['/rss?a=1&b=2'])
    def test_rdf(self):
        self.assertEqual(b.parse_feed('<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/"><item/></rdf:RDF>')[:2],('rss1',1))
    def test_request_ledger_and_no_duplicate(self):
        calls=[]
        def get(url,timeout):
            calls.append((url,timeout))
            return (200,b'<rss><channel/></rss>',.1,None) if url.endswith('/feed') else (404,b'',.1,'404')
        with patch.object(b,'get',get):r=b.probe('example.org',timeout=2)
        self.assertEqual(len(calls),len(r['requests']))
        self.assertEqual(len(calls),len(set(u for u,t in calls)))
        self.assertTrue(all(t==2 for u,t in calls))
    def test_bytes_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input';data=b'Hello.\r\nWorld.\r\n';p.write_bytes(data);out=io.StringIO()
            with contextlib.redirect_stdout(out):a.main(p)
            r=json.loads(out.getvalue());self.assertEqual(r['source_sha256'],hashlib.sha256(data).hexdigest());self.assertEqual(r['source_bytes_utf8'],len(data))
    def test_empty_audit(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input';p.write_text('')
            with self.assertRaisesRegex(ValueError,'at least one'):a.main(p)
    def test_cli_timeout_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            seeds=Path(d)/'seeds';seeds.write_text('test:example.org\n');out=Path(d)/'out'
            record={'robots':{'status':200},'sitemap':{'status':200,'entries':1},'feed':{'parsed_kind':'rss'}}
            with patch.object(b.sys,'argv',['bench',str(seeds),str(out),'--timeout','2']), patch.object(b,'probe',return_value=record) as probe, patch.object(b.time,'sleep'), contextlib.redirect_stderr(io.StringIO()):
                b.main()
            probe.assert_called_once_with('example.org',timeout=2)
            data=json.loads(out.read_text());self.assertEqual(data['timeout_s'],2);self.assertTrue(data['complete'])

    def test_empty_analysis(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input';p.write_text(json.dumps({'run_started_utc':'x','run_finished_utc':'x','results':[]}))
            with contextlib.redirect_stdout(io.StringIO()):z.main(p)
    def test_response_limits_and_bad_gzip(self):
        class Response(io.BytesIO):
            status=200
        for data,headers in [(b'123456',{}),(gzip.compress(b'x'*100),{'Content-Encoding':'gzip'}),(b'broken',{'Content-Encoding':'gzip'})]:
            r=Response(data);r.headers=headers
            with patch.object(b.urllib.request,'urlopen',return_value=r):
                status,body,secs,error=b.get('https://example.org',limit=50 if headers else 5)
            self.assertIsNotNone(error)
    def test_stored_run_totals(self):
        rows=json.loads((ROOT/'dead-web/runs/run_2026-10-31.json').read_text())['results']
        self.assertEqual(sum(z.sitemap_ok(r) or z.feed_ok(r) for r in rows),44)

class PublishedSources(unittest.TestCase):
    def test_embedded_code_matches_repository(self):
        import re, html
        for doc, paths in [('docs/dead-web/index.html', ['dead-web/seeds.txt','dead-web/deadtech_bench.py']), ('docs/magnifying-glass/index.html',['ad-audit/audit_rig.py'])]:
            text=(ROOT/doc).read_text()
            blocks=re.findall(r'<pre>(.*?)</pre>',text,re.S)
            self.assertEqual(len(blocks),len(paths))
            for block,path in zip(blocks,paths):
                data=(ROOT/path).read_bytes()
                self.assertEqual(html.unescape(block),data.decode())
                self.assertIn(hashlib.sha256(data).hexdigest(),text)
    def test_no_withdrawn_age_values_in_table(self):
        text=(ROOT/'docs/dead-web/index.html').read_text()
        self.assertNotIn('739,919.8',text)
        self.assertNotIn('<th>lastmod (d)</th>',text)
    def test_no_success_analysis(self):
        with tempfile.TemporaryDirectory() as d:
            data=json.loads((ROOT/'dead-web/runs/run_2026-10-31.json').read_text())
            data['results']=data['results'][:1]
            data['results'][0]['robots']['status']=403
            data['results'][0]['sitemap']['status']=403
            path=Path(d)/'run';path.write_text(json.dumps(data))
            with contextlib.redirect_stdout(io.StringIO()):z.main(path)

if __name__=='__main__':unittest.main()
