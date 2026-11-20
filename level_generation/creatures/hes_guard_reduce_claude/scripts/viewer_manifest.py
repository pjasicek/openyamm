#!/usr/bin/env python3
"""review/viewer/manifest.json: the approved export (r100, 8,559) and the reduction (r84, 7,189) for ranks A/B/C
(GLBs from viewer_tiers.py + add_rifle.py); clips copied from the source project's viewer manifest (read only)."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
o = json.load(open(ROOT.parent / 'hes_guard_claude' / 'review' / 'viewer' / 'manifest.json'))
for c in o['clips'].values():   # anchor images live in the source project
    for a in c.get('anchors', []):
        a['source_images'] = [x.replace('../../', '../../../hes_guard_claude/', 1) for x in a.get('source_images', [])]
names = {'a': 'A: Landfall Guard (slate blue, red tabard)', 'b': 'B: Guard Sergeant (grey-green)', 'c': "C: Warden's Guard (navy, white)"}
labs = {'r100': 'approved export · 8,559', 'r84': 'reduced · 7,189'}
models = []
for lab in labs:
    for t in 'abc':
        f = f'hes_guard_{lab}_{t}.glb'; h = hashlib.sha256((V / f).read_bytes()).hexdigest()
        models.append({'id': f'{t}_{lab}', 'label': f'{names[t]} · {labs[lab]}', 'revision': 'reduce-1',
                       'url': f'{f}?v={h[:12]}', 'sha256': h})
json.dump({'revision': 'reduce-1', 'default_clip': 'Standing', 'default_model': 'a_r84', 'feedback': 'feedback/user_feedback.json',
           'models': models, 'clips': o['clips']}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models))
