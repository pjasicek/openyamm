#!/usr/bin/env python3
"""review/viewer/manifest.json: the approved export (r100, 7,485; the source project's viewer GLBs with their tier
crests) and the reduction (r80, 5,987; viewer_swap.py on export/hes_glassback.glb, the same crests) for tiers A/B/C;
clips from the source project's viewer manifest (read only)."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
o = json.load(open(ROOT.parent / 'hes_glassback_claude' / 'review' / 'viewer' / 'manifest.json'))
names = {'a': 'A: Glassback Pup (short crest)', 'b': 'B: Glassback (full crest)', 'c': 'C: Glassback Bull (tall crest)'}
labs = {'r100': 'approved export · 7,485', 'r80': 'reduced · 5,987'}
txt = json.dumps(o['clips']).replace('"../../references_hd/', '"../../../hes_glassback_claude/references_hd/')
o['clips'] = json.loads(txt)   # reference images live in the source project
models = []
for lab in labs:
    for t in 'abc':
        f = f'hes_glassback_{lab}_{t}.glb'; h = hashlib.sha256((V / f).read_bytes()).hexdigest()
        models.append({'id': f'{t}_{lab}', 'label': f'{names[t]} · {labs[lab]}', 'revision': 'reduce-1',
                       'url': f'{f}?v={h[:12]}', 'sha256': h})
json.dump({'revision': 'reduce-1', 'model': models[4]['url'].split('?')[0], 'model_sha256': models[4]['sha256'],
           'default_clip': 'Walking', 'default_model': 'b_r80', 'feedback': 'feedback/user_feedback.json',
           'models': models, 'clips': o['clips']}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models))
