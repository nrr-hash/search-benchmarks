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
.methods{margin:2.5rem 0;border-block:1px solid var(--rule);padding:1rem 0}
.methods summary{font-family:var(--mono);font-size:.85rem;cursor:pointer;color:var(--flag);padding:.3rem 0}
.methods[open] summary{margin-bottom:1.5rem}
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
<p class="standfirst">SearchApi’s job ad promises to recognize AI slop. Its own recruiting copy arrives with the familiar corporate fittings and a little picture of a magnifying glass. The picture deserves a closer look.</p>
<p class="byline"><span>Nathaniel Robertson</span><span>2 November 2026</span><span>v1.3</span></p>
<p>Above the section explaining how SearchApi judges applicants sits a magnifying glass. <span role="img" aria-label="Magnifying glass emoji">🔍</span> <code>U+1F50D LEFT-POINTING MAGNIFYING GLASS</code>, to be exact. Four bytes in UTF-8. Two code units in UTF-16. An admirably compact representation of scrutiny.</p>
<p>Below it, the recruitment copy explains how to distinguish real research from AI slop.</p>
<p>The company sells structured search data. Its vacancy asks for someone who can code a benchmark, inspect a result, and publish an inconvenient finding. Excellent requirements. Then the copy appoints itself to the border force of authentic thought.</p>
<p class="pull">“Real research has a rig. AI slop has prose and no reproducible number.”</p>
<p>There it is. A difficult question of judgment has been converted into a sentence that could be printed on a conference tote bag.</p>
<h2>Emoji rigor</h2>
<p>The emojis deserve their own inspection. A target ushers the candidate toward the reasons for joining. A wrench introduces the work. A robot supervises the warning about AI. The responsibilities arrive flexing an arm; the difficulties are on fire. The candidate’s qualifications are dusted with sparkles. They accumulate down the left margin like markers on a drained reservoir, cheerful, weatherproof, and addressed to no one.</p>
<p>By the benefits section, the vacancy has become a reward chart. A little house means remote work. A rising chart means equity; dollar bills mean profit sharing. A brain represents learning from the founder, and an island promises the retreat. The researcher is expected to interrogate evidence, apparently while being guided through the document by pictures of the nouns.
</p><p>The rest of the apparatus is reassuringly familiar. The question about joining. The list of hard parts. The promise of autonomy. The warning that certain readers will not be suitable. The voice insists that the applicant be self-directed. The layout seems unwilling to trust that applicant to reach the next heading without a small illustrated escort. A company demanding original research has furnished its recruiting copy from the standard catalog.</p>
<p>There is a particular corporate serenity in a document that denounces assembled writing while reaching for every fitting in the showroom.</p>
<p>An emoji is not an intellectual offense. The condescension lies in the combination: a stern lecture about standards, packaged with the visual reassurance of a workplace induction game. These conventions are written by humans every day. That is the problem with the ad’s confidence. Recognizing the furniture does not tell you who assembled the room, let alone whether anyone has thought inside it.</p>
<h2>A rig is not an alibi</h2>
<p>Publishing the code behind a benchmark is good practice. It lets another person examine the method, rerun the calculation, and find the mistake. It does not prevent the mistake.</p>
<p>A rig can measure the wrong thing with exquisite consistency. A number can be reproducible and irrelevant. A repository can preserve an unsupported argument in excellent working order. The presence of machinery establishes that machinery was present.</p>
<p>The ad acknowledges AI assistance. It expects the successful candidate to use it. That makes the little binary proclamation stranger still: the actual work requires judgment about methods and evidence, while the slogan offers two labeled bins.</p>
<p>One can imagine the ideal office behind this copy: glass walls, silent doors, and a small red light that comes on when a sentence is insufficiently human. The advert does not explain who calibrated the light.</p>
<h2>What the glass actually finds</h2>
<p>I measured the publisher’s own plain-text field. It contains {a['words']} words under the rig’s declared word-count rule, and {a['machine_writing_tells_present']['emoji_section_header']['count']} matches for its symbol-led heading pattern. The inventory contains {a['emoji']['total_codepoints']} codepoints in the specified symbol ranges, including variation selectors. None of those measurements identifies an author.</p>
<p>The useful distinction is between a count and the claim attached to it. I can reproduce the count. I cannot turn it into a reliable test of human originality by adopting a sufficiently disappointed tone.</p>
<p>The criticism here is editorial: the recruiting voice projects certainty that its own familiar constructions do very little to earn. The typography has been asked to wear a laboratory coat.</p>
<h2>The attention checkpoint</h2>
<p>The ad also asks candidates to include a particular phrase and gives language models an instruction to add a dad joke. The first can check whether an applicant noticed an instruction. A joke left in an application might expose an unattended draft. Neither would establish a general ability to distinguish checked AI assistance from unassisted human writing.</p>
<p><strong>Octopus Tentacle</strong>. The attention checkpoint can reopen.</p>
<p>And, since the ad specifically invites a dad joke:</p>
<p><strong>Why did the crawler and <code>robots.txt</code> stop speaking?</strong><br>One kept setting boundaries. The other kept treating them as advisory.</p>
<p>The recruitment system may now resume its important work.</p>
<p>HR is entitled to ask for careful work. The candidate is entitled to ask what, exactly, the test establishes. A competent answer requires more than the conviction that the hiring side will recognize the bad stuff when it sees it.</p>
<p>The magnifying glass, meanwhile, has already passed the interview. Bright, legible, and entirely untroubled by the distinction between looking closely and appearing to do so.</p>
<p>Four bytes wide. Searching nothing.</p>
</main>
<details class="methods"><summary>Source, measurements, and reproducible code</summary>
<h2>Evidence behind the criticism</h2>
<p>This is a critique of the published recruitment copy and its claims, not an allegation about who wrote it or the quality of SearchApi’s product. The source is the publisher-provided text retrieved on November 2, 2026. The magnifying glass appears beside the section describing applicant evaluation; its Unicode name and encoding widths are recorded in the linked report.</p>
<div class="figs">{fig(a['words'],'regex-counted words')}{fig(a['machine_writing_tells_present']['emoji_section_header']['count'],'heading-pattern matches')}{fig(a['emoji']['total_codepoints'],'symbol-range codepoints')}{fig(4,'magnifying glass UTF-8 bytes')}</div>
<p>The pattern list is not a validated detector. Sentence boundaries and symbol ranges are explicit heuristics, and the data cannot establish authorship or intention.</p>
<h2>The Unicode inventory</h2>
<div class="scroller"><table><caption>Every matched codepoint, in input order</caption><thead><tr><th>Codepoint</th><th>Unicode name</th><th>UTF-8 bytes</th><th>UTF-16 units</th></tr></thead><tbody>{symbols}</tbody></table></div>
<h2>Reproduce the measurement</h2>
<p>Run <code>python3 ad-audit/measure_job.py new-job-report.json</code> from the repository root. It fetches the public job-board API, selects the job ID, measures the exact UTF-8 encoding of <code>descriptionPlain</code>, and records the response hash, input hash, script hash, Python version, and Unicode database version.</p>
<p>The measured input was {a['source_bytes_utf8']:,} bytes. Its SHA-256 is <code class="hash">{a['source_sha256']}</code>. A future live response may differ. Compare hashes before comparing counts; a different representation is a different experiment.</p>
<p><a href="{esc(a['provenance']['job_url'])}">Original vacancy</a> · <a href="{esc(a['provenance']['api_url'])}">Publisher's job-board feed</a> · <a href="https://github.com/nrr-hash/search-benchmarks/blob/main/ad-audit/results/job_2026-11-02.json">Dated report</a> · <a href="https://github.com/nrr-hash/search-benchmarks/blob/main/ad-audit/measure_job.py">Source-fetching script</a></p>
<div class="limits"><h3>Scope</h3><ul><li>The source is the publisher-provided plain-text field retrieved on 2 November 2026. A browser rendering or another export format may differ.</li><li>The copyrighted advertisement is not redistributed here. The live endpoint can change; the recorded hashes identify the measured representation but do not preserve its contents.</li><li>Sentence boundaries and symbol ranges are explicit heuristics. No count establishes authorship, intention, or product quality.</li><li>Code tests check behaviour and arithmetic. They are not independent human approval of the argument.</li></ul></div>
<h2>The code</h2>{pre('ad-audit/audit_rig.py')}
</details>
<footer><p>v1.3 · 2 November 2026. Editorial criticism; code generated and revised with AI assistance. Counts derive from the linked publisher-text report. Dated reports identify their own inputs; compare source hashes before comparing results.</p><p>Code MIT licensed. Prose © Nathaniel Robertson 2026.</p></footer>'''
shell('docs/magnifying-glass/index.html',body)

spec=importlib.util.spec_from_file_location('analysis',ROOT/'dead-web/analyse.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
run_path='dead-web/runs/run_2026-11-02_v1_2.json';d=json.loads((ROOT/run_path).read_text());q=m.summarise(d);c=q['counts'];n=q['n']
category=''.join(f'<tr><td>{esc(k)}</td><td>{v["either"]}/{v["n"]}</td></tr>' for k,v in sorted(q['categories'].items()))
rows=''.join(f'<tr><td>{esc(r["domain"])}</td><td>{esc(r["robots"]["status"] or "no response")}</td><td>{esc(r["sitemap"]["parsed_kind"] if m.sitemap_ok(r) else "not found")}</td><td>{r["sitemap"]["entries"] if m.sitemap_ok(r) else "—"}</td><td>{esc(r["feed"]["parsed_kind"] if m.feed_ok(r) else "not found")}</td><td>{sum(x.get("error")=="deadline exceeded" for x in r["requests"])}</td></tr>' for r in d['results'])
body=nav+f'''<main id="main"><h1>What the dead web still publishes</h1>
<p class="standfirst">Before giving a crawler a job, I checked what the sites were already publishing. A recognized sitemap or feed turned up on {c['either']} of {n} selected domains. Some of the supposedly difficult discovery work was waiting by the front door.</p>
<p class="byline"><span>Nathaniel Robertson</span><span>November 2, 2026</span><span>v1.3</span></p>
<p>The web can resemble a business park after visiting hours: glass frontages, silent lobbies, and systems still announcing themselves to an audience that has moved elsewhere. It is tempting to arrive with more machinery.</p>
<p>I tried the filing cabinet first.</p>
<p>A sitemap can list a site’s URLs. A feed can expose recent entries. These are modest, inspectable ways of publishing structured information. Neither needs to know that a visitor has arrived with a budget for something more elaborate.</p>
<p>SearchApi’s recruitment ad asks for writers who build their own research rigs. Fair enough. Here is one, built to answer a question that ought to come before a purchasing decision: what can these sites already tell us about themselves?</p>
<div class="figs">{fig(c['either'],'sitemap or feed found')}{fig(c['sitemap'],'recognized sitemap roots')}{fig(c['feed'],'recognized feeds')}{fig(c['neither_found'],'neither found by probe')}</div>
<h2>The files nobody has to sell you</h2>
<p>On this fixed list, {c['either']} of {n} domains supplied a recognized sitemap or feed through the checks. That is {100*c['either']/n:.1f} percent of a deliberately varied, hand-picked list, not an estimate of the whole web. One recognized sitemap had no entries. Parsing the label on a filing cabinet does not establish what is inside it.</p>
<p>For an inventory or a change-monitoring task, that is still a useful place to begin. Try the declared structure before making a crawler infer it. The fashionable part of the system may be the part you need least for that particular job.</p>
<h2>The doors that did not open</h2>
<p>The rig found neither supported format on {c['neither_found']} domains. Its {q['requests_recorded']} recorded attempts included {q['deadline_failures']} deadline failures. Those failures belong in the result. Leaving them out would make the route look easier than it was.</p>
<p>They also limit the conclusion. A six-second deadline can stop an experiment before a server supplies its answer. A failed discovery attempt does not establish that a site publishes nothing. The locked door and the empty room are different findings.</p>
<h2>The vendor’s own front door</h2>
<p>SearchApi was one of the five search-data and scraping vendors on the list. Its fallback <code>/sitemap.xml</code> request returned 404 after redirecting to the <code>www</code> host. The <code>robots.txt</code> request hit the deadline. The probe found no supported feed.</p>
<p>A company selling structured discovery is an interesting place for that route to fail. It is not evidence that the company has no sitemap anywhere, still less a benchmark of its product. A 404 is an answer about an address. It is not a character reference.</p>
<h2>Buy the part that does the job</h2>
<p>A sitemap does not tell you where a page ranks, which competitors appear above it, or what a search result page looked like yesterday. Those are different research questions. A SERP API and a site’s own inventory are not interchangeable merely because both contain URLs.</p>
<p>The useful distinction is the job. Use declared structure when the task is discovery and the structure is adequate. Use a different source when the task needs evidence the site’s inventory cannot supply. This experiment compares no paid products and makes no claim about their relative performance.</p>
<p>The apparatus matters. So does asking a question worth attaching it to.</p>
<p>Before commissioning another expedition, check the noticeboard.</p>
</main>
<details class="methods"><summary>Method, dated results, limitations, and code</summary>
<h2>What the probe actually did</h2>
<p>The run took place on November 2, 2026, from {esc(q['run_started_utc'][11:19])} to {esc(q['run_finished_utc'][11:19])} UTC. Exact timestamps are in the dated JSON. Rig v1.2 used eight concurrent domain workers, with requests within a domain made sequentially and a 0.4-second pause between attempts. Each request had a six-second elapsed deadline covering worker startup, DNS, redirects, body reads, and decompression.</p>
<p>For each domain: fetch <code>robots.txt</code>; try up to five declared sitemaps and the conventional fallback until a recognised sitemap root is found; fetch the homepage; try up to ten declared RSS or Atom links, then six conventional feed paths. RSS 2.0, RSS 1.0, and Atom are recognised. Final redirect URLs are recorded, and relative feed links are resolved against the final homepage and its first HTML base URL.</p>
<p>Recognised means the XML root matches a supported format. It does not mean that the file is populated, complete, correctly maintained, or that its listed URLs resolve. One of the {c['sitemap']} recognised sitemap roots had zero entries.</p>
<h2>Results by category</h2>
<div class="scroller"><table><caption>Either supported sitemap or feed found; five selected domains per category</caption><thead><tr><th>Category</th><th>Found / tested</th></tr></thead><tbody>{category}</tbody></table></div>
<p>Category totals are descriptive. Five hand-picked sites cannot establish that an industry is better at publishing structured data, or explain the intent of the people maintaining those sites.</p>
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
</details>
<footer><p>v1.3 · 2 November 2026. Scripts generated and revised with AI assistance. Counts are computed from the linked run; local response-body hashes and selected parse results were checked by code. This is model-run verification, not independent human sign-off.</p><p>Code MIT licensed. Prose © Nathaniel Robertson 2026. Earlier dated runs remain separate; method changes prevent treating the difference as a web-wide trend.</p></footer>'''
shell('docs/dead-web/index.html',body)
(ROOT/'dead-web/results').mkdir(exist_ok=True)
(ROOT/'dead-web/results/summary_2026-11-02.json').write_text(json.dumps(q,indent=2)+'\n')
