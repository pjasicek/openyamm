"""Rebuild the external-return review inventory from retained intakes and current queue state."""
import collections
import csv
import html
import json
import os
from pathlib import Path
from urllib.parse import quote

import import_chat_returns as intake

OUT = intake.HERE / 'chat_returns'
q = intake.module.Queue()
rows, bundles, diagnostics, unreturned_details = [], [], [], []
reports = {path: json.loads(path.read_text()) for path in sorted(OUT.glob('*/intake.json'))}
superseded = {Path(r['reconciliation']['prior_intake']) for r in reports.values()
              if r.get('reconciliation') and 'counts' in r}
for path, report in reports.items():
    if path in superseded:
        continue
    bundles.append(dict(bundle=report['bundle'], **report['counts'], intake=str(path)))
    diagnostics.extend(report['diagnostic_decode_failures'])
    unreturned_details.extend(dict(bundle=report['bundle'], **item) for item in report.get('unreturned_details', []))
    for c in report['cells']:
        cell = c['cell']
        current = q.state['cells'].get(cell, {})
        rows.append(dict(bundle=report['bundle'], sheet=c['sheet'], cell=cell,
            status=current.get('status', 'review_pending'), attempt=c['attempt'],
            artifact=c.get('artifact', ''), raw=str(path.parent/'incoming/outputs/raw'/(c['sheet']+'.png')),
            comparisons=c.get('review_images', []), registration=c.get('registration_record', ''),
            footprint='pass' if 'artifact' in c and not c['failures'] else 'fail' if 'artifact' in c else 'raw_only',
            failures=c.get('failures', {}), notes=current.get('reason', ''),
            worker_review=c['worker_review'], prompt_provenance=c['prompt_provenance']))
counts = dict(collections.Counter(r['status'] for r in rows))
unreturned = [{**a, 'cell': c} for c, a in q.state['external_assignments'].items() if a['status']=='assigned']
summary = dict(bundles=bundles, returned_attempts=len({r['attempt'] for r in rows}),
    returned_assets=len(rows), candidates=sum(bool(r['artifact']) for r in rows), statuses=counts,
    still_assigned=len(unreturned), unreturned=unreturned, diagnostic_decode_failures=diagnostics,
    unreturned_details=unreturned_details,
    historical_intakes=sorted(str(p) for p in superseded),
    cells=rows, runtime_review='Pending for newly staged art; no default runtime installation performed.')
intake.save(OUT/'inventory.json', summary)
with (OUT/'inventory.csv').open('w', newline='') as stream:
    fields = ['bundle', 'sheet', 'cell', 'status', 'footprint', 'artifact', 'raw', 'registration', 'notes']
    writer = csv.DictWriter(stream, fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)


def link(path, label):
    return '<a href="%s">%s</a>' % (quote(os.path.relpath(path, OUT)), html.escape(label))


cards = []
for r in rows:
    pictures = ''.join('<a href="%s"><img loading="lazy" src="%s" alt="Native x2, restored x2, overlay"></a>' %
        (quote(os.path.relpath(p, OUT)), quote(os.path.relpath(p, OUT))) for p in r['comparisons'])
    links = [link(r['raw'], 'Raw sheet')]
    if r['artifact']:
        links.extend([link(r['artifact'], 'Candidate PNG'), link(r['registration'], 'Registration evidence')])
    cards.append('<article data-status="%s" data-bundle="%s"><h2>%s</h2><p>%s · %s · footprint: %s</p>%s'
        '<p>%s</p><p>%s</p><details><summary>Worker findings and provenance</summary><pre>%s</pre></details></article>' %
        (r['status'], r['bundle'], html.escape(r['cell']), r['bundle'], r['sheet'], r['footprint'], pictures,
         ' | '.join(links), html.escape(r['notes'] or 'Locally accepted; see registration and queue review.'),
         html.escape(json.dumps(dict(worker=r['worker_review'], failures=r['failures'],
                                    prompt_provenance=r['prompt_provenance']), indent=2))))
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Restoration returns</title>
<style>body{font:16px system-ui;margin:24px;background:#222;color:#eee}a{color:#9dcfff}
header{position:sticky;top:0;background:#222;padding:12px;z-index:1}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(450px,1fr));gap:16px}
article{background:#333;padding:16px;border-radius:8px;min-width:0}h2{font-size:16px;overflow-wrap:anywhere}
img{max-width:100%;height:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}input,select{padding:8px;margin:4px}</style>
<header><h1>Returned restoration candidates</h1><p>666 returned assets. Candidate intake is separate from visual acceptance.
Only 2 locally reviewed assets are staged; other candidates remain unfinished. Full comparisons open at native image size.
For opaque portraits, a passing rectangle/alpha check does not verify facial landmarks or identity.</p>
<input id="search" placeholder="Search filename or notes" aria-label="Search filename or notes">
<select id="status" aria-label="Status"><option value="">All statuses</option><option>accepted</option><option>review_pending</option><option>deferred</option></select>
<select id="bundle" aria-label="Bundle"><option value="">All bundles</option>'''
page += ''.join('<option>%s</option>' % b['bundle'] for b in bundles)
page += '</select><span id="count"></span></header><main>' + '\n'.join(cards) + '''</main>
<script>const cards=[...document.querySelectorAll('article')];const search=document.querySelector('#search');
const status=document.querySelector('#status');const bundle=document.querySelector('#bundle');
function filter(){let count=0;for(const c of cards){c.hidden=!!((status.value&&c.dataset.status!==status.value)||
(bundle.value&&c.dataset.bundle!==bundle.value)||!c.textContent.toLowerCase().includes(search.value.toLowerCase()));if(!c.hidden)count++;}
document.querySelector('#count').textContent=count+' shown';}for(const e of [search,status,bundle])e.addEventListener('input',filter);filter();</script></html>'''
page = page.replace('666 returned assets', str(len(rows))+' returned assets').replace('Only 2 locally reviewed',
    'Only '+str(counts.get('accepted', 0))+' locally reviewed')
(OUT/'index.html').write_text(page)
print(json.dumps(dict(returned=len(rows), candidates=summary['candidates'], states=counts,
                     still_assigned=len(unreturned), corrupt_diagnostics=len(diagnostics))))
