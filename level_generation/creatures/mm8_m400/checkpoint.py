from pathlib import Path
import json,hashlib,datetime
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
g=json.loads((ROOT/'generation.json').read_text())
for key in ('identity','native_w_v0','native_w_v1'):
 refs=['raw/identity_v1.png'] if key=='identity' else [f'references/{key}_matte.png','checkpoints/identity_accepted_v1.png']
 g['batches'][key]['references']=[dict(path=p,sha256=sha(ROOT/p)) for p in refs]
for key,b in g['batches'].items():
 for p in [b['raw'],b['prompt'],*b['references']]:assert sha(ROOT/p['path'])==p['sha256'],(key,p)
(ROOT/'generation.json').write_text(json.dumps(g,indent=2)+'\n')
p=ROOT.parent/'mm8_remaining/progress.json';d=json.loads(p.read_text());d['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
d['families']['m400'].update(status='partial',processed_frames=170,resume='All native frames processed. Finish final_variants and edge contacts, runtime atlas viewer animation checks, then write reviewed validation and refresh inventory. No final manifest exists yet.')
p.write_text(json.dumps(d,indent=2)+'\n')
print('All 26 selected generation prompts/raws/references verified; partial ledger checkpoint saved')
