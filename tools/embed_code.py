"""Refresh embedded source and SHA-256 labels without changing article prose."""
import hashlib
import html
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
def main():
    for doc, files in [('docs/dead-web/index.html', ['dead-web/seeds.txt', 'dead-web/deadtech_bench.py']),
                       ('docs/magnifying-glass/index.html', ['ad-audit/audit_rig.py'])]:
        paths = iter(files)
        def replace(match):
            data = (ROOT / next(paths)).read_bytes()
            caption = re.sub(r'sha256 [0-9a-f]{64}', 'sha256 '+hashlib.sha256(data).hexdigest(), match[1])
            return caption+'<pre>'+html.escape(data.decode(), quote=True)+'</pre>'
        path = ROOT / doc
        path.write_text(re.sub(r'(<figure class="prewrap"><figcaption>.*?</figcaption>)<pre>.*?</pre>',
                               replace, path.read_text(), flags=re.S), encoding='utf-8')
if __name__ == '__main__':
    main()
