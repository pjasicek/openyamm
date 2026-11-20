#!/usr/bin/env python3
"""review/viewer/manifest.json: batch F export (r100) and the reduction for tiers A/B/C (GLBs from viewer_tiers.py,
the unchanged broadsword added by viewer_sword.py); clips copied from the original project's viewer manifest (read only).
Usage: viewer_manifest.py <reduced label, e.g. r81> <source tris> <reduced tris>"""
import hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
lab_r, n_src, n_red = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
o = json.load(open(ROOT.parent / 'mm7_m246_claude' / 'review' / 'viewer' / 'manifest.json'))
names = {'a': 'Goblin - A', 'b': 'Hobgoblin - B', 'c': 'Goblin Lord - C'}
labs = {'r100': f'batch F export · {n_src:,}', lab_r: f'reduced · {n_red:,}'}
models = []
for lab in labs:
    for t in 'abc':
        f = f'mm7_m246_{lab}_{t}.glb'; h = hashlib.sha256((V / f).read_bytes()).hexdigest()
        models.append({'id': f'{t}_{lab}', 'label': f'{names[t]} · {labs[lab]}', 'revision': 'reduce-1',
                       'url': f'{f}?v={h[:12]}', 'sha256': h})
json.dump({'revision': 'reduce-1', 'default_clip': o.get('default_clip', 'Walking'), 'default_model': f'a_{lab_r}',
           'feedback': 'feedback/user_feedback.json', 'models': models, 'clips': o['clips']}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models))
