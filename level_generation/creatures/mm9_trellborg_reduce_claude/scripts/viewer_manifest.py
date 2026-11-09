#!/usr/bin/env python3
"""review/viewer/manifest.json: the installed r18 (13,881) and the reduction r85m (11,801) for tiers A/B/C (GLBs from
viewer_tiers.py); clips copied from the creature project's viewer manifest (read only), anchor images pointed there."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; V = ROOT / 'review' / 'viewer'
o = json.load(open(ROOT.parent / 'mm9_lizardorc_claude' / 'review' / 'viewer' / 'manifest.json'))
for c in o['clips'].values():
    for a in c.get('anchors', []):
        a['source_images'] = [x.replace('../../', '../../../mm9_lizardorc_claude/', 1) for x in a.get('source_images', [])]
names = {'a': 'A: Lizard-Orc (row 189)', 'b': 'B: Lizard-Orc Warrior (row 190)', 'c': 'C: Lizard-Orc Mage (row 191)'}
labs = {'before': 'installed r18 · 13,881', 'r85m': 'reduced r85m · 11,801'}
models = []
for t in 'abc':
    for lab in labs:
        f = f'liz_{t}_{lab}.glb'; h = hashlib.sha256((V / f).read_bytes()).hexdigest()
        models.append({'id': f'{t}_{lab}', 'label': f'{names[t]} · {labs[lab]}', 'revision': 'reduce-1', 'url': f'{f}?v={h[:12]}', 'sha256': h})
json.dump({'revision': 'reduce-1', 'model': 'liz_a_r85m.glb', 'default_clip': 'Standing', 'default_model': 'a_r85m',
           'feedback': 'feedback/user_feedback.json', 'models': models, 'clips': o['clips']}, open(V / 'manifest.json', 'w'), indent=1)
print('MANIFEST', len(models), 'models', len(o['clips']), 'clips')
