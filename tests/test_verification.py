"""Evidence gates must remain active under Python optimisation."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verify_run', ROOT / 'tools/verify_run.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class Verification(unittest.TestCase):
    def fixture(self, folder):
        body = b'<urlset><url/></urlset>'
        (folder / 'bodies').mkdir()
        (folder / 'bodies/one.gz').write_bytes(gzip.compress(body))
        request = {'url': 'https://example.org/sitemap.xml', 'status': 200,
                   'bytes': len(body), 'body_file': 'bodies/one.gz',
                   'body_sha256': hashlib.sha256(body).hexdigest()}
        row = {'domain': 'example.org', 'requests': [request],
               'sitemap': {'status': 200, 'url': request['url'],
                           'parsed_kind': 'urlset', 'entries': 1},
               'feed': {'status': 404}}
        return {'complete': True, 'seed_count': 1, 'results': [row]}

    def test_tampering_rejected_with_and_without_optimisation(self):
        for optimise in (False, True):
            for fault in ('none', 'hash', 'size', 'count', 'duplicate'):
                with self.subTest(optimise=optimise, fault=fault), tempfile.TemporaryDirectory() as temp:
                    folder = Path(temp)
                    data = self.fixture(folder)
                    row = data['results'][0]
                    if fault == 'hash':
                        row['requests'][0]['body_sha256'] = '0' * 64
                    elif fault == 'size':
                        row['requests'][0]['bytes'] += 1
                    elif fault == 'count':
                        row['sitemap']['entries'] = 2
                    elif fault == 'duplicate':
                        data['results'].append(row)
                        data['seed_count'] = 2
                    path = folder / 'run.json'
                    path.write_text(json.dumps(data))
                    command = [sys.executable] + (['-O'] if optimise else [])
                    result = subprocess.run(command + [str(ROOT / 'tools/verify_run.py'), str(path)],
                                            capture_output=True, text=True)
                    if fault == 'none':
                        self.assertEqual(result.returncode, 0, result.stderr)
                    else:
                        self.assertNotEqual(result.returncode, 0, fault)

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp)
            target = Path(outside) / 'body.gz'
            body = b'outside'
            target.write_bytes(gzip.compress(body))
            (root / 'link.gz').symlink_to(target)
            with self.assertRaisesRegex(ValueError, 'invalid body path'):
                verifier.read_body(root, {'body_file': 'link.gz', 'bytes': len(body),
                                         'body_sha256': hashlib.sha256(body).hexdigest()})

    def test_repository_gate_active_with_optimisation(self):
        command = "import runpy; m=runpy.run_path('tools/check_repository.py'); m['require'](False, 'deliberate corruption')"
        result = subprocess.run([sys.executable, '-O', '-c', command], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('deliberate corruption', result.stderr)

    def test_failed_rebuild_check_does_not_overwrite_articles(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp) / 'repository'
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns('__pycache__', '.git'))
            article = copy / 'docs/dead-web/index.html'
            changed = article.read_bytes().replace(b'The web can resemble', b'This web can resemble', 1)
            self.assertNotEqual(changed, article.read_bytes())
            article.write_bytes(changed)
            result = subprocess.run([sys.executable, str(copy/'tools/check_repository.py')],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('not reproducible', result.stderr)
            self.assertEqual(article.read_bytes(), changed, 'checker overwrote article prose')
