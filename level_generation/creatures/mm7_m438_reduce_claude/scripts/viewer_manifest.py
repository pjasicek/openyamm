#!/usr/bin/env python3
"""review/viewer/manifest.json: the batch F export (r100: 9,499 body + 1,844 forearm) and the reduction (r78: 7,407 +
1,458) for tiers A/B/C (GLBs from viewer_tiers.py + viewer_forearm.py); clips copied from the production project's
viewer manifest (read only)."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
o = json.load(open(ROOT.parent / 'mm7_m438_claude' / 'review' / 'viewer' / 'manifest.json'))
names = {'a': 'Rotted Corpse - A', 'b': 'Walking Dead - B', 'c': 'Zombie - C'}
labs = {'r100': 'batch F export · 9,499 + forearm 1,844', 'r78': 'reduced · 7,407 + forearm 1,458'}
# anchor images live in the production project
for c in o['clips'].values():
    for a in c.get('anchors', []):
        a['source_images'] = [x.replace('../../references_native/', '../../../mm7_m438_claude/references_native/') for x in a.get('source_images', [])]
models = []
for lab in labs:
    for t in 'abc':
        f = f'mm7_m438_{lab}_{t}.glb'; h = hashlib.sha256((V / f).read_bytes()).hexdigest()
        models.append({'id': f'{t}_{lab}', 'label': f'{names[t]} · {labs[lab]}', 'revision': 'reduce-1',
                       'url': f'{f}?v={h[:12]}', 'sha256': h})
json.dump({'revision': 'reduce-1', 'default_clip': o.get('default_clip', 'Standing'), 'default_model': 'a_r78',
           'feedback': 'feedback/user_feedback.json', 'models': models, 'clips': o['clips']}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models))
