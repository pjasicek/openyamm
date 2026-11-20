#!/usr/bin/env python3
"""review/viewer/manifest.json: the approved export (r100, 4,396; the source project's viewer GLBs) and the reduction
(r87, 3,846; viewer_swap.py on export/hes_drone.glb) for tiers A/B/C with their gear; clips from the source project's
viewer manifest (read only)."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
o = json.load(open(ROOT.parent / 'hes_drone_claude' / 'review' / 'viewer' / 'manifest.json'))
names = {'a': 'A: Seeker Drone', 'b': 'B: Hunter Drone (twin emitter)', 'c': 'C: Reaver Drone (shield ring)'}
labs = {'r100': 'approved export · 4,396', 'r87': 'reduced · 3,846'}
models = []
for lab in labs:
    for t in 'abc':
        f = f'hes_drone_{lab}_{t}.glb'; h = hashlib.sha256((V / f).read_bytes()).hexdigest()
        models.append({'id': f'{t}_{lab}', 'label': f'{names[t]} · {labs[lab]}', 'revision': 'reduce-1',
                       'url': f'{f}?v={h[:12]}', 'sha256': h})
json.dump({'revision': 'reduce-1', 'model': models[3]['url'].split('?')[0], 'model_sha256': models[3]['sha256'],
           'default_clip': 'Standing', 'default_model': 'a_r87', 'feedback': 'feedback/user_feedback.json',
           'models': models, 'clips': o['clips']}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models))
