#!/usr/bin/env python3
"""review/viewer/manifest.json: the batch G v7 export (r100) and the reduced body (r79) for tiers A/B/C
(GLBs from viewer_tiers.py); clips copied from the original project's viewer manifest (read only)."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
o = json.load(open(ROOT.parent / 'mm7_m150_claude' / 'review' / 'viewer' / 'manifest.json'))
names = {'a': 'Angel - A (green skirt)', 'b': 'Angel Lord - B (blue skirt)', 'c': 'Archangel - C (magenta skirt)'}
labs = {'r100': 'v7 body · 9,916', 'r79': 'reduced body · 7,828'}
models = []
for lab in labs:
    for t in 'abc':
        f = f'mm7_m150_{lab}_{t}.glb'; h = hashlib.sha256((V / f).read_bytes()).hexdigest()
        models.append({'id': f'{t}_{lab}', 'label': f'{names[t]} · {labs[lab]}', 'revision': 'reduce-1',
                       'url': f'{f}?v={h[:12]}', 'sha256': h})
json.dump({'revision': 'reduce-1', 'default_clip': 'Standing', 'default_model': 'a_r79', 'feedback': 'feedback/user_feedback.json',
           'models': models, 'clips': o['clips']}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models))
