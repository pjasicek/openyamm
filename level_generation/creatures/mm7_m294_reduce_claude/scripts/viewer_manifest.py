#!/usr/bin/env python3
"""review/viewer/manifest.json: batch F export (r100) and the reduction (r76) for tiers A/B/C (GLBs from
viewer_tiers.py, full-detail mesh only); clips copied from the original project's viewer manifest (read only).
Copied from mm7_m262_reduce_claude."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
o = json.load(open(ROOT.parent / 'mm7_m294_claude' / 'review' / 'viewer' / 'manifest.json'))
names = {'a': 'Necromancer - A', 'b': 'Speaker for the Dead - B', 'c': 'Queen of the Dead - C'}
labs = {'r100': 'batch F export · 12,015', 'r76': 'reduced 76 % · 9,125'}
models = []
for lab in labs:
    for t in 'abc':
        f = f'mm7_m294_{lab}_{t}.glb'; h = hashlib.sha256((V / f).read_bytes()).hexdigest()
        models.append({'id': f'{t}_{lab}', 'label': f'{names[t]} · {labs[lab]}', 'revision': 'reduce-1',
                       'url': f'{f}?v={h[:12]}', 'sha256': h})
json.dump({'revision': 'reduce-1', 'default_clip': o.get('default_clip', 'Standing'), 'default_model': 'a_r76',
           'feedback': 'feedback/user_feedback.json', 'models': models, 'clips': o['clips']}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models))
