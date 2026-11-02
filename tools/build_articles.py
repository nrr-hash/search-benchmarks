from pathlib import Path
import json,html,re,importlib.util
ROOT=Path(__file__).resolve().parents[1]
def esc(x):return html.escape(str(x),quote=True)
def localize(body):
 parts=re.split(r'(<pre\b[^>]*>.*?</pre>|<code\b[^>]*>.*?</code>)',body,flags=re.S)
 changes={'Recognised':'Recognized','recognised':'recognized','recognises':'recognizes','recognise':'recognize','normalisation':'normalization','normalising':'normalizing','behaviour':'behavior','labelled':'labeled','localisation':'localization','analysed':'analyzed','per cent':'percent','2 November 2026':'November 2, 2026'}
 for i in range(0,len(parts),2):
  for old,new in changes.items():parts[i]=parts[i].replace(old,new)
 return ''.join(parts)
def shell(path,body):
 body=localize(body)
 def keep_last_pair(match):
  pair=match.group(1)
  return (pair.rsplit(' ',1)[0]+'&nbsp;'+pair.rsplit(' ',1)[1] if len(html.unescape(pair)) < 40 else pair)+match.group(2)
 body=re.sub(r'([^\s<>]+ [^\s<>]+)(</p>)',keep_last_pair,body)
 p=ROOT/path;s=p.read_text().replace('lang="en-GB"','lang="en-US"');s=s[:s.index('<body>')]+'<body>\n<div class="wrap">\n'+body+'\n</div>\n</body>\n</html>\n'
 s=re.sub(r'\n\*\{box-sizing:border-box\}.*?(?=</style>)','',s,flags=re.S)
 s=s.replace('</style>','''
*{box-sizing:border-box}
h1{text-align:center;max-width:20ch;margin-inline:auto}
p,li{text-wrap:pretty}
:focus-visible{outline:3px solid var(--flag);outline-offset:4px}
nav{font-family:var(--mono);font-size:.8rem;margin-bottom:1.7rem;display:flex;flex-wrap:wrap;gap:.8rem 1.3rem}
pre{max-height:32rem;overscroll-behavior:contain}
.prewrap figcaption{overflow-wrap:anywhere}
.scroller:focus-visible{outline-offset:2px}
@media(max-width:480px){.wrap{padding-top:2rem}h1{font-size:2.1rem}.figs{grid-template-columns:repeat(2,minmax(0,1fr))}.fig{min-width:0}.fig .n{font-size:1.5rem}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style>''')
 s=s.replace('<div class="scroller">','<div class="scroller" tabindex="0" role="region" aria-label="Scrollable data table">')
 s=re.sub(r'<th>(.*?)</th>',r'<th scope="col">\1</th>',s)
 p.write_text(s)
def fig(value,label):return f'<div class="fig"><span class="n">{esc(value)}</span><span class="l">{esc(label)}</span></div>'
def pre(path):return '<figure class="prewrap"><figcaption>'+esc(Path(path).name)+' sha256 '+__import__('hashlib').sha256((ROOT/path).read_bytes()).hexdigest()+'</figcaption><pre>'+esc((ROOT/path).read_text())+'</pre></figure>'
nav='<nav aria-label="Article navigation"><a href="../">All measurements</a><a href="https://github.com/nrr-hash/search-benchmarks">Code and data</a></nav>'
a=json.loads((ROOT/'ad-audit/results/job_2026-11-02.json').read_text());stats=a['sentence_length']
symbols=''.join(f'<tr><td>{esc(r["codepoint"])}</td><td>{esc(r["unicode_name"])}</td><td>{r["utf8_bytes"]}</td><td>{r["utf16_code_units"]}</td></tr>' for r in a['emoji']['codepoints'])
body=nav+f'''<main id="main"><h1>The magnifying glass problem</h1>
<p class="standfirst">The publisher's plain-text field contains {a['words']} counted words and no standalone backslashes. The method reproduces those counts. It cannot tell you who wrote the advertisement.</p>
<p class="byline"><span>Nathaniel Robertson</span><span>2 November 2026</span><span>v1.2</span></p>
<p>I built a source-fetching script, measured the publisher’s plain-text field, and published the input hash and output. The test separates an inspectable count from a claim about authorship.</p>
<p>The careers page loads its vacancies from Ashby. I selected the advertised job by its identifier and measured the API's <code>descriptionPlain</code> field exactly as supplied, without reconstructing it from a screenshot, pasted Markdown, or browser layout.</p>
<div class="figs">{fig(a['words'],'regex-counted words')}{fig(a['sentences'],'heuristic sentences')}{fig(a['emoji']['total_codepoints'],'symbol-range codepoints')}{fig(a['machine_writing_tells_present'].get('stray_trailing_backslash',{}).get('count',0),'standalone backslashes')}</div>
<h2>Start with the publisher’s representation</h2>
<p>The retrieved publisher text contains no standalone backslash lines. That is a finding about the supplied plain-text field. Copying through Markdown, extracting rendered HTML, and reading an API field can produce different text; a rigorous comparison names the representation before discussing its apparent defects.</p>
<p>The same restraint applies to the symbols. This input contains {a['emoji']['total_codepoints']} codepoints in the rig's declared ranges. That is a count of codepoints, including variation selectors, rather than a count of pictures or perceived characters. The script is not a complete Unicode emoji implementation.</p>
<p>UTF-8 and UTF-16 widths are useful engineering facts. They do not establish that a search engine cannot interpret a heading, that a writer used AI, or that the surrounding argument is weak. Those would be separate questions requiring separate tests.</p>
<p class="pull">A reproducible count answers a defined question. It does not validate every conclusion written beside it.</p>
<h2>What the numbers establish</h2>
<p>The word counter recognises ASCII letters and digits, with internal apostrophes and hyphens. Its {a['words']} words are reproducible under that definition, rather than a universal linguistic count. The sentence splitter reports {a['sentences']} segments. Headings, lists, abbreviations, and fragments make that a heuristic partition.</p>
<p>Those segment lengths have a mean of {stats['mean']} words, a median of {stats['median']}, and a population standard deviation of {stats['sd']}. Their coefficient of variation is {stats['coefficient_of_variation']}; the rig's lag-1 estimator gives {stats['lag1_autocorrelation']}. These describe this representation of this document. They are not validated authorship signals.</p>
<p>{len(a['machine_writing_tells_present'])} surface-pattern families match. The script publishes their names and counts in the JSON. The list has no labelled validation corpus, and ordinary human writing matches these constructions. Calling the output a detector would turn a descriptive tool into an unsupported claim.</p>
<h2>The Unicode inventory</h2>
<div class="scroller"><table><caption>Every matched codepoint, in input order</caption><thead><tr><th>Codepoint</th><th>Unicode name</th><th>UTF-8 bytes</th><th>UTF-16 units</th></tr></thead><tbody>{symbols}</tbody></table></div>
<h2>Reproduce the measurement</h2>
<p>Run <code>python3 ad-audit/measure_job.py new-job-report.json</code> from the repository root. It fetches the public job-board API, selects the job ID, measures the exact UTF-8 encoding of <code>descriptionPlain</code>, and records the response hash, input hash, script hash, Python version, and Unicode database version.</p>
<p>The measured input was {a['source_bytes_utf8']:,} bytes. Its SHA-256 is <code class="hash">{a['source_sha256']}</code>. A future live response may differ. Compare hashes before comparing counts; a different representation is a different experiment.</p>
<p><a href="{esc(a['provenance']['job_url'])}">Original vacancy</a> · <a href="{esc(a['provenance']['api_url'])}">Publisher's job-board feed</a> · <a href="https://github.com/nrr-hash/search-benchmarks/blob/main/ad-audit/results/job_2026-11-02.json">Dated report</a> · <a href="https://github.com/nrr-hash/search-benchmarks/blob/main/ad-audit/measure_job.py">Source-fetching script</a></p>
<div class="limits"><h3>Scope</h3><ul><li>The source is the publisher-provided plain-text field retrieved on 2 November 2026. A browser rendering or another export format may differ.</li><li>The copyrighted advertisement is not redistributed here. The live endpoint can change; the recorded hashes identify the measured representation but do not preserve its contents.</li><li>Sentence boundaries and symbol ranges are explicit heuristics. No count establishes authorship, intention, or product quality.</li><li>Code tests check behaviour and arithmetic. They are not independent human approval of the argument.</li></ul></div>
<h2>The code</h2>{pre('ad-audit/audit_rig.py')}
<p>Use the source-fetching script to check the input, the audit script to reproduce the count, and the stated limits to judge the claim. That is the handoff another engineer needs.</p></main>
<footer><p>v1.2 · 2 November 2026. Code generated and revised with AI assistance. Counts derive from the linked publisher-text report. Dated reports identify their own inputs; compare source hashes before comparing results.</p><p>Code MIT licensed. Prose © Nathaniel Robertson 2026.</p></footer>'''
shell('docs/magnifying-glass/index.html',body)

spec=importlib.util.spec_from_file_location('analysis',ROOT/'dead-web/analyse.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
run_path='dead-web/runs/run_2026-11-02_v1_2.json';d=json.loads((ROOT/run_path).read_text());q=m.summarise(d);c=q['counts'];n=q['n']
category=''.join(f'<tr><td>{esc(k)}</td><td>{v["either"]}/{v["n"]}</td></tr>' for k,v in sorted(q['categories'].items()))
rows=''.join(f'<tr><td>{esc(r["domain"])}</td><td>{esc(r["robots"]["status"] or "no response")}</td><td>{esc(r["sitemap"]["parsed_kind"] if m.sitemap_ok(r) else "not found")}</td><td>{r["sitemap"]["entries"] if m.sitemap_ok(r) else "—"}</td><td>{esc(r["feed"]["parsed_kind"] if m.feed_ok(r) else "not found")}</td><td>{sum(x.get("error")=="deadline exceeded" for x in r["requests"])}</td></tr>' for r in d['results'])
body=nav+f'''<main id="main"><h1>What the dead web still publishes</h1>
<p class="standfirst">A fresh probe found a recognized sitemap or feed on {c['either']} of {n} selected domains. Before paying for discovery, check what a site already publishes, and distinguish a missing result from an unanswered request.</p>
<p class="byline"><span>Nathaniel Robertson</span><span>2 November 2026</span><span>v1.2</span></p>
<p>A sitemap can supply a list of URLs without making a crawler discover every link itself. A feed can expose recent entries. Neither tells you where a page ranks in a search engine. That distinction decides which job the free structured web can do, and which job needs a different source.</p>
<p>I tested a fixed list of {n} domains across 12 categories, five per category. It is deliberately varied and hand-picked. It is not representative of the web, and the percentages below describe only this list, this method, and this execution environment.</p>
<div class="figs">{fig(c['either'],'sitemap or feed found')}{fig(c['sitemap'],'recognised sitemap roots')}{fig(c['feed'],'recognised feeds')}{fig(c['neither_found'],'neither found by probe')}</div>
<h2>What the probe actually did</h2>
<p>The run took place on November 2, 2026, from {esc(q['run_started_utc'][11:19])} to {esc(q['run_finished_utc'][11:19])} UTC. Exact timestamps are in the dated JSON. Rig v1.2 used eight concurrent domain workers, with requests within a domain made sequentially and a 0.4-second pause between attempts. Each request had a six-second elapsed deadline covering worker startup, DNS, redirects, body reads, and decompression.</p>
<p>For each domain: fetch <code>robots.txt</code>; try up to five declared sitemaps and the conventional fallback until a recognised sitemap root is found; fetch the homepage; try up to ten declared RSS or Atom links, then six conventional feed paths. RSS 2.0, RSS 1.0, and Atom are recognised. Final redirect URLs are recorded, and relative feed links are resolved against the final homepage and its first HTML base URL.</p>
<p>Recognised means the XML root matches a supported format. It does not mean that the file is populated, complete, correctly maintained, or that its listed URLs resolve. One of the {c['sitemap']} recognised sitemap roots had zero entries.</p>
<h2>The useful number, and its denominator</h2>
<p>{c['either']} of {n} domains, {100*c['either']/n:.1f} per cent, supplied at least one supported format through these checks. {c['neither_found']} did not. The latter is a failed discovery result, not a claim that those sites publish nothing.</p>
<p>The request ledger contains {q['requests_recorded']} explicit attempts, including {q['deadline_failures']} deadline failures. That is a substantial access limitation. A different deadline, network, execution environment, user-agent, or discovery route could find more. No inferred bot policy is assigned to a timeout, a reset, or a bare HTTP status.</p>
<p class="pull">The probe can prove that it retrieved a structured file. A failed request cannot prove that the file does not exist.</p>
<p>Elapsed timings are published in the JSON summary, with denominators. They include client overhead and automatic redirects, and the six-second deadline censors slower observations. They are useful for explaining this run's cost, not for ranking servers or comparing directly with the earlier v1.0 run.</p>
<h2>Results by category</h2>
<div class="scroller"><table><caption>Either supported sitemap or feed found; five selected domains per category</caption><thead><tr><th>Category</th><th>Found / tested</th></tr></thead><tbody>{category}</tbody></table></div>
<p>Category totals are descriptive. Five hand-picked sites cannot establish that an industry is better at publishing structured data, or explain the intent of the people maintaining those sites.</p>
<h2>What this means for a research job</h2>
<p>For a content inventory, start with a site's own declarations and test whether they are useful. That may remove an unnecessary discovery pass. For historical search results, ranking, or search-engine features, use a source that actually measures those things. A sitemap is not a substitute for a SERP API.</p>
<p>This experiment does not benchmark SearchApi's product, any competing vendor's product, or paid crawling. It measures the availability of selected public endpoints through one stated procedure. A fair product comparison would need a shared task, ground truth, repeated runs, and comparable access conditions.</p>
<div class="limits"><h3>Scope</h3><ul><li>No random sampling, geographic comparison, controlled time series, or estimate of the whole web.</li><li>Sitemap indexes are not traversed. Their entry counts refer to child sitemap elements, while URL sets count URL elements.</li><li>Discovery is bounded: first five declared sitemaps, first ten homepage feed links, and six fallback feed paths. Omitted candidates are counted in the JSON.</li><li>Publisher timestamps are declarations. This article makes no verified content-freshness claim from them.</li><li>HTTP timings include subprocess startup and transfer overhead. Request deadlines and network conditions materially affect the findings.</li></ul></div>
<h2>Reproduce it</h2>
<p>From the repository root:</p><pre>python3 dead-web/deadtech_bench.py dead-web/seeds.txt new-run.json --timeout 6 --workers 8 --pause 0.4
python3 dead-web/analyse.py new-run.json --json
python3 tools/verify_run.py new-run.json</pre>
<p>Use a new output filename. The run records its seed hash, script hash, Python version, timeout, concurrency, pacing, every explicit request, final redirect URLs where available, and decoded-body hashes. The CLI also saves decoded response bodies locally so its selected parse results can be independently checked. The repository publishes extracted evidence and hashes; it does not redistribute homepage or feed contents.</p>
<p><a href="https://github.com/nrr-hash/search-benchmarks/blob/main/{run_path}">Dated run</a> · <a href="https://github.com/nrr-hash/search-benchmarks/blob/main/dead-web/results/summary_2026-11-02.json">Machine-readable summary</a> · <a href="https://github.com/nrr-hash/search-benchmarks/blob/main/dead-web/seeds.txt">Fixed seed list</a> · <a href="https://github.com/nrr-hash/search-benchmarks/blob/main/dead-web/results/evidence_2026-11-02.json.gz">Extracted evidence</a></p>
<h2>Full results</h2>
<div class="scroller"><table><caption>Endpoint detections and per-domain deadline failures, 2 November 2026</caption><thead><tr><th>Domain</th><th>robots status</th><th>Sitemap root</th><th>Entries</th><th>Feed</th><th>Deadlines</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>The code</h2>{pre('dead-web/seeds.txt')}{pre('dead-web/deadtech_bench.py')}
<p>The practical decision is small and testable: inspect a site's structured declarations before designing a discovery pipeline, and budget for the cases where that route fails.</p></main>
<footer><p>v1.2 · 2 November 2026. Scripts generated and revised with AI assistance. Counts are computed from the linked run; local response-body hashes and selected parse results were checked by code. This is model-run verification, not independent human sign-off.</p><p>Code MIT licensed. Prose © Nathaniel Robertson 2026. Earlier dated runs remain separate; method changes prevent treating the difference as a web-wide trend.</p></footer>'''
shell('docs/dead-web/index.html',body)
(ROOT/'dead-web/results').mkdir(exist_ok=True)
(ROOT/'dead-web/results/summary_2026-11-02.json').write_text(json.dumps(q,indent=2)+'\n')
