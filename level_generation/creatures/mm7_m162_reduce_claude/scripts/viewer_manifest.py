#!/usr/bin/env python3
"""review/viewer/manifest.json: Batch E export (r100), reduced smooth (r75) and reduced flat (r75f) for tiers A/B/C
(GLBs from viewer_tiers.py); clips copied from the original project's viewer manifest (read only)."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
o = json.load(open(ROOT.parent / 'mm7_m162_claude' / 'review' / 'viewer' / 'manifest.json'))
names = {'a': 'Young Behemoth - A (green)', 'b': 'Behemoth - B (blue-violet)', 'c': 'Ancient Behemoth - C (red)'}
labs = {'r100': 'Batch E export · 14,752', 'r75': 'reduced 75 % smooth · 11,063', 'r75f': 'reduced 75 % flat · 11,063'}
models = []
for lab in labs:
    for t in 'abc':
        f = f'mm7_m162_{lab}_{t}.glb'; h = hashlib.sha256((V / f).read_bytes()).hexdigest()
        models.append({'id': f'{t}_{lab}', 'label': f'{names[t]} · {labs[lab]}', 'revision': 'reduce-1',
                       'url': f'{f}?v={h[:12]}', 'sha256': h})
json.dump({'revision': 'reduce-1', 'default_clip': 'Standing', 'default_model': 'a_r75', 'feedback': 'feedback/user_feedback.json',
           'models': models, 'clips': o['clips']}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models))
