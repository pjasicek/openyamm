#!/usr/bin/env python3
"""review/viewer/manifest.json: batch G export (r100) and the reduction (r66) for tiers A/B/C
(GLBs from viewer_tiers.py); clips copied from the original project's viewer manifest (read only)."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
o = json.load(open(ROOT.parent / 'mm7_m234_claude' / 'review' / 'viewer' / 'manifest.json'))
names = {'a': 'Stone Gargoyle - A (green)', 'b': 'Marble Gargoyle - B (blue)', 'c': 'Obsidian Gargoyle - C (red)'}
labs = {'r100': 'batch G export · 10,812', 'r66': 'reduced 66 % · 7,134'}
models = []
for lab in labs:
    for t in 'abc':
        f = f'mm7_m234_{lab}_{t}.glb'; h = hashlib.sha256((V / f).read_bytes()).hexdigest()
        models.append({'id': f'{t}_{lab}', 'label': f'{names[t]} · {labs[lab]}', 'revision': 'reduce-1',
                       'url': f'{f}?v={h[:12]}', 'sha256': h})
json.dump({'revision': 'reduce-1', 'default_clip': 'Standing', 'default_model': 'a_r66', 'feedback': 'feedback/user_feedback.json',
           'models': models, 'clips': o['clips']}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models))
